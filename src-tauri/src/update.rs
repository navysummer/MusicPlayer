use anyhow::{bail, Context, Result};
use serde::Serialize;
use std::time::Duration;

const REPO_OWNER: &str = "navysummer";
const REPO_NAME: &str = "MusicPlayer";

#[derive(Debug, Serialize)]
pub struct UpdateInfo {
    pub current_version: String,
    pub latest_version: String,
    pub has_release: bool,
    pub has_update: bool,
    pub url: String,
    pub name: String,
    pub notes: String,
}

pub fn check_update(current_version: &str) -> Result<UpdateInfo> {
    let url = format!(
        "https://api.github.com/repos/{}/{}/releases?per_page=10",
        REPO_OWNER, REPO_NAME
    );

    let user_agent = format!("{}-{}/{}", REPO_OWNER, REPO_NAME, env!("CARGO_PKG_VERSION"));

    let resp = ureq::get(&url)
        .set("User-Agent", &user_agent)
        .set("Accept", "application/vnd.github+json")
        .timeout(Duration::from_secs(12))
        .call();

    let body: serde_json::Value = match resp {
        Ok(r) => r.into_json().context("解析 GitHub 响应失败")?,
        Err(ureq::Error::Status(code, _)) => {
            if code == 403 || code == 429 {
                bail!("GitHub 访问受限（可能触发限流），请稍后再试");
            }
            bail!("GitHub 返回错误状态码：{}", code);
        }
        Err(ureq::Error::Transport(_)) => {
            bail!("无法连接 GitHub，请检查网络后重试");
        }
    };

    let mut latest_tag = "";
    let mut latest_url = "";
    let mut latest_name = "";
    let mut latest_notes = "";

    if let Some(arr) = body.as_array() {
        for item in arr {
            if item["draft"].as_bool().unwrap_or(false) {
                continue;
            }
            if item["prerelease"].as_bool().unwrap_or(false) {
                continue;
            }
            latest_tag = item["tag_name"].as_str().unwrap_or("");
            latest_url = item["html_url"].as_str().unwrap_or("");
            latest_name = item["name"].as_str().unwrap_or(latest_tag);
            latest_notes = item["body"].as_str().unwrap_or("");
            break;
        }
    }

    let latest_version = latest_tag.trim_start_matches('v').to_string();
    let has_release = !latest_version.is_empty();
    let has_update = has_release && compare_versions(current_version, &latest_version);

    Ok(UpdateInfo {
        current_version: current_version.to_string(),
        latest_version: if has_release {
            latest_version
        } else {
            "暂无".to_string()
        },
        has_release,
        has_update,
        url: latest_url.to_string(),
        name: latest_name.to_string(),
        notes: latest_notes.to_string(),
    })
}

fn compare_versions(current: &str, latest: &str) -> bool {
    fn to_nums(s: &str) -> Vec<u32> {
        s.split(|c: char| !c.is_ascii_digit())
            .filter_map(|p| p.parse().ok())
            .collect()
    }
    let cur = to_nums(current);
    let lat = to_nums(latest);
    for (i, lv) in lat.iter().enumerate() {
        let cv = cur.get(i).copied().unwrap_or(0);
        if lv > &cv {
            return true;
        }
        if lv < &cv {
            return false;
        }
    }
    false
}