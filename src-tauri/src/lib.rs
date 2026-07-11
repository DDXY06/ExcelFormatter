use std::process::Command;
use std::path::PathBuf;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessResult {
    pub status: String,
    pub total: Option<f64>,
    pub temp_state: Option<String>,
    pub output_path: Option<String>,
    pub message: Option<String>,
}

#[tauri::command]
async fn process_file(source_path: String, company_name: String) -> Result<ProcessResult, String> {
    let python_script = get_python_script_path()?;

    let output = Command::new("python")
        .arg(&python_script)
        .arg("process")
        .arg(&source_path)
        .arg(&company_name)
        .current_dir(project_root())
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let result: ProcessResult = serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse Python output: {} — raw: {}", e, stdout))?;

    Ok(result)
}

#[tauri::command]
async fn apply_iva_decision(temp_state: String, apply_iva: bool) -> Result<ProcessResult, String> {
    let python_script = get_python_script_path()?;

    let apply_flag = if apply_iva { "1" } else { "0" };

    let output = Command::new("python")
        .arg(&python_script)
        .arg("apply_iva")
        .arg(&temp_state)
        .arg(apply_flag)
        .current_dir(project_root())
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let result: ProcessResult = serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse Python output: {} — raw: {}", e, stdout))?;

    Ok(result)
}

fn project_root() -> PathBuf {
    let mut dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    dir.pop();
    dir
}

fn get_python_script_path() -> Result<PathBuf, String> {
    let mut path = project_root();
    path.push("Script");
    path.push("app_workflow.py");
    if !path.exists() {
        return Err(format!("Python script not found at {:?}", path));
    }
    Ok(path)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![process_file, apply_iva_decision])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
