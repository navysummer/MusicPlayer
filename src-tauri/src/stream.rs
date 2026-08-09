use anyhow::Result;
use std::fs::File;
use std::io::Read;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;
use tiny_http::{Header, Response, Server};

pub struct StreamServer {
    port: u16,
    handle: Option<thread::JoinHandle<()>>,
    stop_flag: Arc<AtomicBool>,
    bytes_written: Arc<AtomicU64>,
    active: Arc<AtomicBool>,
}

impl StreamServer {
    pub fn new() -> Self {
        StreamServer {
            port: 0,
            handle: None,
            stop_flag: Arc::new(AtomicBool::new(false)),
            bytes_written: Arc::new(AtomicU64::new(0)),
            active: Arc::new(AtomicBool::new(false)),
        }
    }

    pub fn start(&mut self) -> Result<u16> {
        self.stop_flag.store(false, Ordering::SeqCst);
        let server = Server::http("127.0.0.1:0")
            .map_err(|e| anyhow::anyhow!("Failed to start server: {}", e))?;
        self.port = server.server_addr().to_ip().unwrap().port();
        let stop_flag = self.stop_flag.clone();
        let bytes_written = self.bytes_written.clone();
        let active = self.active.clone();

        let handle = thread::spawn(move || {
            loop {
                if stop_flag.load(Ordering::SeqCst) {
                    break;
                }
                let request = match server.recv_timeout(std::time::Duration::from_millis(500)) {
                    Ok(Some(r)) => r,
                    Ok(None) => continue,
                    Err(_) => break,
                };

                let url = request.url().to_string();
                let path = url
                    .strip_prefix("/stream?path=")
                    .or_else(|| url.strip_prefix("/stream?path="))
                    .map(|p| urlencoding_decode(p))
                    .unwrap_or_default();

                if path.is_empty() {
                    let response = Response::from_string("Invalid path")
                        .with_status_code(400);
                    let _ = request.respond(response);
                    continue;
                }

                active.store(true, Ordering::SeqCst);

                let file = match File::open(&path) {
                    Ok(f) => f,
                    Err(e) => {
                        let response = Response::from_string(format!("File not found: {}", e))
                            .with_status_code(404);
                        let _ = request.respond(response);
                        continue;
                    }
                };

                let file_size = match file.metadata() {
                    Ok(m) => m.len(),
                    Err(_) => 0,
                };

                let range_header = request.headers().iter().find(|h| {
                    h.field.to_string().to_lowercase() == "range"
                });

                let (start, end) = if let Some(rh) = range_header {
                    parse_range(rh.value.as_str(), file_size)
                } else {
                    (0, file_size.saturating_sub(1))
                };

                let content_length = end - start + 1;
                let is_partial = start > 0 || end < file_size.saturating_sub(1);

                let mut buf = vec![0u8; content_length as usize];
                let mut file = File::open(&path).unwrap();
                use std::io::Seek;
                file.seek(std::io::SeekFrom::Start(start)).ok();
                let read = file.read(&mut buf).unwrap_or(0);
                buf.truncate(read);

                if is_partial {
                    let range_header_str = format!("bytes {}-{}/{}", start, end, file_size);
                    let response = Response::from_data(buf)
                        .with_status_code(206)
                        .with_header(
                            Header::from_bytes(
                                &b"Content-Range"[..],
                                range_header_str.as_bytes(),
                            )
                            .unwrap(),
                        )
                        .with_header(
                            Header::from_bytes(
                                &b"Accept-Ranges"[..],
                                b"bytes",
                            )
                            .unwrap(),
                        );

                    let _ = request.respond(response);
                } else {
                    let response = Response::from_data(buf).with_header(
                        Header::from_bytes(&b"Accept-Ranges"[..], b"bytes").unwrap(),
                    );
                    let _ = request.respond(response);
                }

                bytes_written.fetch_add(read as u64, Ordering::SeqCst);
            }
            active.store(false, Ordering::SeqCst);
        });

        self.handle = Some(handle);
        Ok(self.port)
    }

    pub fn stop(&mut self) {
        self.stop_flag.store(true, Ordering::SeqCst);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }

    pub fn port(&self) -> u16 {
        self.port
    }

    pub fn bytes_written(&self) -> u64 {
        self.bytes_written.load(Ordering::SeqCst)
    }

    pub fn is_active(&self) -> bool {
        self.active.load(Ordering::SeqCst)
    }
}

fn urlencoding_decode(s: &str) -> String {
    let mut result = String::new();
    let mut chars = s.chars();
    while let Some(c) = chars.next() {
        if c == '%' {
            let hex: String = chars.by_ref().take(2).collect();
            if let Ok(byte) = u8::from_str_radix(&hex, 16) {
                result.push(byte as char);
            }
        } else {
            result.push(c);
        }
    }
    result
}

fn parse_range(range: &str, file_size: u64) -> (u64, u64) {
    let range = range.trim_start_matches("bytes=");
    let parts: Vec<&str> = range.split('-').collect();
    let start: u64 = parts.first().and_then(|s| s.parse().ok()).unwrap_or(0);
    let end: u64 = parts
        .get(1)
        .and_then(|s| {
            if s.is_empty() {
                None
            } else {
                s.parse().ok()
            }
        })
        .unwrap_or(file_size.saturating_sub(1));
    (start, end.min(file_size.saturating_sub(1)))
}