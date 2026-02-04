use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Fast parser for study plan text without regex
/// Parses "Day X:" patterns and extracts content between them
#[pyfunction]
fn parse_study_plan(py: Python, plan_text: &str) -> PyResult<Vec<PyObject>> {
    let bytes = plan_text.as_bytes();
    let len = bytes.len();
    let mut result = Vec::new();
    let mut pos = 0;

    while pos < len {
        // Skip whitespace
        while pos < len && (bytes[pos] == b' ' || bytes[pos] == b'\t' || 
                           bytes[pos] == b'\n' || bytes[pos] == b'\r') {
            pos += 1;
        }

        if pos >= len {
            break;
        }

        // Check for "Day " pattern (case-sensitive for performance)
        if pos + 4 <= len && 
           bytes[pos] == b'D' && 
           bytes[pos + 1] == b'a' && 
           bytes[pos + 2] == b'y' && 
           bytes[pos + 3] == b' ' {
            
            let day_start = pos;
            pos += 4; // Move past "Day "

            // Parse the number
            let num_start = pos;
            while pos < len && bytes[pos].is_ascii_digit() {
                pos += 1;
            }

            // Must have at least one digit
            if pos == num_start {
                pos = day_start + 1;
                continue;
            }

            // Check for colon
            if pos < len && bytes[pos] == b':' {
                pos += 1; // Include the colon
                let day_end = pos;

                // Extract day label
                let day_label = unsafe {
                    // SAFETY: We know this is valid UTF-8 substring from original string
                    std::str::from_utf8_unchecked(&bytes[day_start..day_end])
                };

                // Skip whitespace after colon
                while pos < len && (bytes[pos] == b' ' || bytes[pos] == b'\t') {
                    pos += 1;
                }

                // Skip newlines after the day label
                while pos < len && (bytes[pos] == b'\n' || bytes[pos] == b'\r') {
                    pos += 1;
                }

                let content_start = pos;

                // Find content until next "Day " pattern or end
                let mut content_end = pos;
                while pos < len {
                    // Look ahead for next "Day " pattern
                    if pos + 4 <= len && 
                       bytes[pos] == b'D' && 
                       bytes[pos + 1] == b'a' && 
                       bytes[pos + 2] == b'y' && 
                       bytes[pos + 3] == b' ' {
                        // Check if it's a valid day pattern (followed by digit)
                        if pos + 5 <= len && bytes[pos + 4].is_ascii_digit() {
                            break;
                        }
                    }
                    content_end = pos + 1;
                    pos += 1;
                }

                // Extract and trim content
                let content = if content_start < content_end {
                    let raw_content = unsafe {
                        std::str::from_utf8_unchecked(&bytes[content_start..content_end])
                    };
                    raw_content.trim()
                } else {
                    ""
                };

                // Create Python dict for this entry
                let dict = PyDict::new(py);
                dict.set_item("day", day_label)?;
                dict.set_item("tasks", content)?;
                result.push(dict.into());

                // Reset position to start of next day
                pos = content_end;
            } else {
                // Not a valid day pattern, continue searching
                pos = day_start + 1;
            }
        } else {
            pos += 1;
        }
    }

    Ok(result)
}

/// Python module definition
#[pymodule]
fn study_plan_parser(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_study_plan, m)?)?;
    Ok(())
}
