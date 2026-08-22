// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::net::TcpStream;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

/// Resolve the backend launcher command for the current environment.
fn backend_command() -> (String, Vec<String>) {
    // Allow overriding via env var (useful in dev and packaging).
    if let Ok(custom) = env::var("MINDVAULT_BACKEND") {
        if let Some((bin, args)) = custom.split_once(' ') {
            return (bin.to_string(), args.split(' ').map(String::from).collect());
        }
        return (custom, vec![]);
    }
    // Production: launch the bundled Python backend from the same process.
    // The launcher starts a local server and opens the browser — but in the
    // desktop shell we point the webview at it instead.
    if let Ok(exe) = env::var("MINVAULT_BACKEND_EXE") {
        return (exe, vec![]);
    }
    // Development default: `python -m mindvault` from the repo backend dir.
    ("python".to_string(), vec!["-m".to_string(), "mindvault".to_string()])
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Start the local backend as a child process.
            let (bin, args) = backend_command();
            let child = Command::new(&bin)
                .args(&args)
                .env("MV_HOST", "127.0.0.1")
                .env("MV_PORT", "8000")
                .spawn()
                .expect("failed to start MindVault backend");

            // Wait for the backend to become healthy before showing the UI.
            let mut ready = false;
            for _ in 0..60 {
                if TcpStream::connect("127.0.0.1:8000").is_ok() {
                    ready = true;
                    break;
                }
                thread::sleep(Duration::from_millis(500));
            }
            if !ready {
                eprintln!("MindVault backend did not start in time.");
            }

            app.manage(BackendProcess(Mutex::new(Some(child))));

            let window = app.get_webview_window("main").unwrap();
            if ready {
                let _ = window.navigate("http://127.0.0.1:8000".parse().unwrap());
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            // On close, stop the backend child process.
            if let tauri::WindowEvent::Destroyed = event {
                let app = window.app_handle();
                if let Some(state) = app.try_state::<BackendProcess>() {
                    let mut guard = state.0.lock().unwrap();
                    if let Some(mut child) = guard.take() {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running MindVault");
}
