---
name: calculate-sha256
description: Calculate the SHA-256 hash of a given text. (Forensics / IR standard)
---

# Calculate SHA-256

This skill calculates the **SHA-256** hash of a given text using the Web Crypto API.  
SHA-256 is the current industry standard for digital forensics and incident response evidence integrity.

## Examples

* "Calculate sha256 of Incident Response Toolkit test string"
* "What is the SHA-256 hash of the file evidence.txt?"
* "Hash this password with SHA-256"

## Instructions

Call the `run_js` tool with the following exact parameters:

- script name: `index.html`
- data: A JSON string with the following field
  - text: the text to calculate SHA-256 hash for
