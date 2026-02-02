use pyo3::prelude::*;
use pyo3::types::PyDict;

const MAX_QUESTIONS: usize = 20;
const CORRECT_MARKER: &[u8] = b"|CORRECT:";
const MIN_QUESTION_LENGTH: usize = 10;
const MIN_ANSWER_LENGTH: usize = 1;

#[derive(Debug)]
struct QuestionBlock {
    start: usize,
    end: usize,
    correct: char,
}

#[derive(Debug)]
struct ParsedQuestion<'a> {
    text: &'a str,
    answers: [&'a str; 4],
    correct: char,
}

/// Ultra-fast, safe, and robust quiz parser
#[pyfunction]
fn parse_quiz(py: Python, quiz: &str) -> PyResult<PyObject> {
    // Early validation
    if quiz.is_empty() {
        return Ok(PyDict::new_bound(py).to_object(py));
    }
    
    let bytes = quiz.as_bytes();
    
    // Step 1: Extract all question blocks
    let blocks = extract_blocks(bytes)?;
    
    if blocks.is_empty() {
        return Ok(PyDict::new_bound(py).to_object(py));
    }
    
    // Step 2: Parse each block
    let questions_dict = PyDict::new_bound(py);
    let mut question_count = 0;
    
    for block in blocks.iter().take(MAX_QUESTIONS) {
        if let Some(parsed) = parse_block(bytes, block) {
            if is_valid_question(&parsed) {
                let dict = create_question_dict(py, &parsed)?;
                question_count += 1;
                questions_dict.set_item(question_count.to_string(), dict)?;
            }
        }
    }
    
    Ok(questions_dict.to_object(py))
}

/// Extract all question blocks with their correct answers
#[inline]
fn extract_blocks(bytes: &[u8]) -> PyResult<Vec<QuestionBlock>> {
    let mut blocks = Vec::with_capacity(MAX_QUESTIONS);
    let mut current_start = 0;
    let len = bytes.len();
    
    // Use optimized search
    let mut i = 0;
    while i < len.saturating_sub(CORRECT_MARKER.len()) {
        // Fast path: check first and last byte before full comparison
        if bytes[i] == b'|' && bytes[i + 8] == b':' {
            // Verify full pattern
            if &bytes[i..i + CORRECT_MARKER.len()] == CORRECT_MARKER {
                let block_end = i;
                i += CORRECT_MARKER.len();
                
                // Skip whitespace
                while i < len && bytes[i].is_ascii_whitespace() {
                    i += 1;
                }
                
                // Extract correct answer
                let correct = if i < len {
                    normalize_answer_char(bytes[i] as char)
                } else {
                    continue; // Invalid block
                };
                
                // Find end delimiter
                while i < len && bytes[i] != b'|' {
                    i += 1;
                }
                
                if i < len {
                    i += 1; // Skip |
                    
                    // Validate block size
                    if block_end > current_start && block_end - current_start >= MIN_QUESTION_LENGTH {
                        blocks.push(QuestionBlock {
                            start: current_start,
                            end: block_end,
                            correct,
                        });
                    }
                    
                    current_start = i;
                }
            } else {
                i += 1;
            }
        } else {
            i += 1;
        }
    }
    
    Ok(blocks)
}

/// Parse a single question block
#[inline]
fn parse_block<'a>(bytes: &'a [u8], block: &QuestionBlock) -> Option<ParsedQuestion<'a>> {
    let slice = &bytes[block.start..block.end];
    
    // Skip leading whitespace and question number
    let pos = skip_whitespace_and_number(slice)?;
    
    // Find all option positions
    let option_positions = find_option_positions(&slice[pos..])?;
    
    // Extract question text (everything before first option)
    let question_end = pos + option_positions[0].0;
    let question_text = safe_trim_to_str(&slice[pos..question_end])?;
    
    // Extract all answers
    let mut answers = [""; 4];
    for i in 0..4 {
        let (_, content_start) = option_positions[i];
        let content_end = if i < 3 {
            option_positions[i + 1].0
        } else {
            slice.len() - pos
        };
        
        let answer_slice = &slice[pos + content_start..pos + content_end];
        answers[i] = safe_trim_answer_to_str(answer_slice)?;
    }
    
    Some(ParsedQuestion {
        text: question_text,
        answers,
        correct: block.correct,
    })
}

/// Find positions of all four options (a, b, c, d)
#[inline]
fn find_option_positions(slice: &[u8]) -> Option<[(usize, usize); 4]> {
    let mut positions = [(0, 0); 4];
    let mut found_mask = 0u8; // Bitmask to track which options we've found
    
    let len = slice.len();
    let mut i = 0;
    
    while i < len.saturating_sub(1) && found_mask != 0b1111 {
        let b = slice[i];
        
        // Check if this is an option label
        if b >= b'a' && b <= b'd' && slice[i + 1] == b')' {
            let idx = (b - b'a') as usize;
            
            // Only record first occurrence of each option
            if (found_mask & (1 << idx)) == 0 {
                positions[idx] = (i, i + 2);
                found_mask |= 1 << idx;
            }
            
            i += 2;
        } else {
            i += 1;
        }
    }
    
    // Verify all four options were found
    if found_mask == 0b1111 {
        Some(positions)
    } else {
        None
    }
}

/// Skip leading whitespace and question number
#[inline]
fn skip_whitespace_and_number(slice: &[u8]) -> Option<usize> {
    let mut pos = 0;
    let len = slice.len();
    
    // Skip whitespace
    while pos < len && slice[pos].is_ascii_whitespace() {
        pos += 1;
    }
    
    // Skip digits
    while pos < len && slice[pos].is_ascii_digit() {
        pos += 1;
    }
    
    // Skip whitespace after number
    while pos < len && slice[pos].is_ascii_whitespace() {
        pos += 1;
    }
    
    if pos < len {
        Some(pos)
    } else {
        None
    }
}

/// Safely convert bytes to str with trimming
#[inline(always)]
fn safe_trim_to_str(bytes: &[u8]) -> Option<&str> {
    let trimmed = trim_bytes(bytes);
    std::str::from_utf8(trimmed).ok()
}

/// Safely convert answer bytes to str with aggressive trimming
#[inline(always)]
fn safe_trim_answer_to_str(bytes: &[u8]) -> Option<&str> {
    let trimmed = trim_answer_bytes(bytes);
    if trimmed.len() >= MIN_ANSWER_LENGTH {
        std::str::from_utf8(trimmed).ok()
    } else {
        None
    }
}

/// Trim whitespace from byte slice
#[inline(always)]
fn trim_bytes(bytes: &[u8]) -> &[u8] {
    let mut start = 0;
    let mut end = bytes.len();
    
    while start < end && bytes[start].is_ascii_whitespace() {
        start += 1;
    }
    
    while end > start && bytes[end - 1].is_ascii_whitespace() {
        end -= 1;
    }
    
    &bytes[start..end]
}

/// Trim whitespace and punctuation from answer
#[inline(always)]
fn trim_answer_bytes(bytes: &[u8]) -> &[u8] {
    let mut start = 0;
    let mut end = bytes.len();
    
    // Trim start
    while start < end && bytes[start].is_ascii_whitespace() {
        start += 1;
    }
    
    // Trim end (including punctuation)
    while end > start {
        let b = bytes[end - 1];
        if b.is_ascii_whitespace() || matches!(b, b'.' | b',' | b'!' | b'?' | b';' | b':') {
            end -= 1;
        } else {
            break;
        }
    }
    
    &bytes[start..end]
}

/// Normalize answer character (lowercase, validate)
#[inline(always)]
fn normalize_answer_char(c: char) -> char {
    match c.to_ascii_lowercase() {
        'a' | 'b' | 'c' | 'd' => c.to_ascii_lowercase(),
        _ => 'a', // Default fallback
    }
}

/// Validate parsed question
#[inline]
fn is_valid_question(q: &ParsedQuestion) -> bool {
    // Question text must not be empty
    if q.text.is_empty() || q.text.len() < 5 {
        return false;
    }
    
    // All answers must be non-empty
    for answer in &q.answers {
        if answer.is_empty() {
            return false;
        }
    }
    
    // Correct answer must be valid
    matches!(q.correct, 'a' | 'b' | 'c' | 'd')
}

/// Create Python dict from parsed question
#[inline]
fn create_question_dict<'a>(py: Python<'a>, q: &'a ParsedQuestion<'a>) -> PyResult<Bound<'a, PyDict>> {
    let dict = PyDict::new_bound(py);
    let answers_dict = PyDict::new_bound(py);
    
    answers_dict.set_item("a", q.answers[0])?;
    answers_dict.set_item("b", q.answers[1])?;
    answers_dict.set_item("c", q.answers[2])?;
    answers_dict.set_item("d", q.answers[3])?;
    
    dict.set_item("question", q.text)?;
    dict.set_item("answers", answers_dict)?;
    dict.set_item("correct", q.correct)?;
    
    Ok(dict)
}

#[pymodule]
fn quiz_parser(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_quiz, m)?)?;
    Ok(())
}