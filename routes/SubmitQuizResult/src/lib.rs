use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

#[pyfunction]
fn submit_result<'py>(
    py: Python<'py>,
    quiz: Bound<'py, PyDict>,
    user_answers: Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyDict>> {
    let total = quiz.len();
    
    if total == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err("No quiz data"));
    }
    
    // Extract everything to Rust types in one go
    let mut quiz_data: Vec<(String, String)> = Vec::with_capacity(total);
    
    for (key, value) in quiz.iter() {
        let question_num = key.extract::<String>()?;
        let question_dict = value.downcast::<PyDict>()?;
        
        let correct = question_dict
            .get_item("correct")?
            .and_then(|v| if v.is_none() { None } else { v.extract::<String>().ok() })
            .unwrap_or_default();
        
        quiz_data.push((question_num, correct));
    }
    
    // Extract user answers to HashMap
    let user_data: HashMap<String, String> = user_answers
        .iter()
        .filter_map(|(k, v)| {
            if v.is_none() {
                None
            } else {
                Some((k.extract().ok()?, v.extract().ok()?))
            }
        })
        .collect();
    
    // NOW release GIL and do pure Rust computation
    let (score, results) = py.allow_threads(|| {
        let mut score = 0usize;
        let mut results: Vec<(String, String, String, bool)> = Vec::with_capacity(total);
        
        for (question_num, correct) in quiz_data {
            let user = user_data.get(&question_num).map(|s| s.as_str()).unwrap_or("");
            
            let is_correct = !correct.is_empty() && correct.eq_ignore_ascii_case(user);
            score += is_correct as usize;
            
            results.push((question_num, correct, user.to_string(), is_correct));
        }
        
        (score, results)
    });
    
    // Convert back to Python
    let percentage = ((score as f64 / total as f64) * 1000.0).round() / 10.0;
    
    let results_dict = PyDict::new(py);
    for (num, correct, user, right) in results {
        let result = PyDict::new(py);
        result.set_item("correct", correct)?;
        result.set_item("user", user)?;
        result.set_item("right", right)?;
        results_dict.set_item(num, result)?;
    }
    
    let final_dict = PyDict::new(py);
    final_dict.set_item("score", score)?;
    final_dict.set_item("total", total)?;
    final_dict.set_item("percentage", percentage)?;
    final_dict.set_item("results", results_dict)?;
    
    Ok(final_dict)
}

#[pymodule]
fn submit_quiz(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(submit_result, module)?)?;
    Ok(())
}
