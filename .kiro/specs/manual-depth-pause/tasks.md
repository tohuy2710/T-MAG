# Implementation Plan: Manual Depth Pause Feature

## Overview

This feature implements a human-in-the-loop workflow for extracting alpha templates from research papers during the depth phase. The system generates comprehensive LLM-ready extraction prompts, pauses execution to allow manual template creation, detects newly created templates, and hot-reloads them into the mining loop.

## Tasks

- [ ] 1. Implement helper functions for data loading
  - [ ] 1.1 Implement load_skill_content() function
    - Read SKILL.md file with UTF-8 encoding
    - Return placeholder text if file not found
    - Handle encoding errors gracefully
    - _Requirements: 10.1, 10.2, 10.3, 10.5_
  
  - [ ] 1.2 Implement load_research_target() function
    - Load config/research_target.json
    - Parse JSON content
    - Raise FileNotFoundError if missing (blocking error)
    - _Requirements: 1.6, 12.3_
  
  - [ ] 1.3 Implement load_field_catalog() function
    - Get field catalog path from research_target.json
    - Load and parse field catalog JSON
    - Return empty list if catalog unavailable
    - Log warnings for missing files
    - _Requirements: 1.3, 9.9, 12.3_
  
  - [ ] 1.4 Implement load_example_templates() function
    - Scan templates/ directory for JSON files
    - Load first 2-3 template files as examples
    - Limit field_pairs to 2 examples per template
    - Skip invalid JSON files with warnings
    - Return empty list if < 2 templates available (triggers error in prompt generation)
    - _Requirements: 1.5, 12.1, 12.2, 13.8_

- [ ] 2. Implement field catalog formatting
  - [ ] 2.1 Implement format_field_catalog_for_prompt() function
    - Group fields by category attribute
    - Sort fields within category by alphaCount descending
    - Select up to 100 total fields across categories
    - Display up to 10 fields per category as examples
    - Include all fields if category has < 10 total
    - Format with markdown bold category headers
    - Add ellipsis showing remaining count when truncated
    - Display total available field count at top
    - _Requirements: 1.3, 1.4, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.10_

- [ ] 3. Implement prompt generation system
  - [ ] 3.1 Implement generate_extraction_prompt() function
    - Combine paper content, SKILL content, field catalog, and examples
    - Include paper content limited to 10,000 characters
    - Include SKILL knowledge from sections 4, 6, 10
    - Include formatted field catalog summary (50-100 fields)
    - Include 2-3 example templates with essential fields
    - Include target configuration (region, universe, delay, neutralizations)
    - Include explicit schema instructions with required fields
    - Include output format instructions (JSON array only, no markdown)
    - Include field usage restrictions (only from catalog)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 10.2, 10.4_
  
  - [ ] 3.2 Implement smart truncation for oversized content
    - Check if assembled prompt exceeds 100,000 characters
    - If yes, reduce field catalog to 50 fields minimum
    - If yes, reduce example templates to 2 minimum
    - Rebuild prompt with reduced content
    - Log warning if still exceeds limit after reduction
    - _Requirements: 1.10, 1.14_
  
  - [ ] 3.3 Implement paper content truncation
    - Truncate paper content at 10,000 characters
    - Use smart truncation: first 8,000 + "[... TRUNCATED ...]" + last 2,000
    - Handle papers shorter than 10,000 characters without truncation
    - _Requirements: 1.1, 1.10, 11.7, 11.8_
  
  - [ ] 3.4 Add error handling for missing dependencies
    - Check for SKILL.md existence before prompt generation
    - Check for config/research_target.json existence
    - Check for at least 2 template examples
    - Generate error responses with specific reasons
    - Log errors and mark paper as extraction_failed
    - _Requirements: 1.11, 1.12, 1.13_

- [ ] 4. Implement file I/O operations
  - [ ] 4.1 Implement save_extraction_prompt() function
    - Write prompt to ._fuel_prompt.txt in workspace root
    - Use UTF-8 encoding
    - Overwrite existing file if present
    - Log file path and character count at INFO level
    - Return True on success, False on failure
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ] 4.2 Add error handling for file write failures
    - Catch exceptions during file write
    - Log error with file path and exception message
    - Mark paper status as extraction_failed
    - Save papers_registry immediately
    - Return False from fuel_one_paper_manual
    - _Requirements: 2.5, 14.9_

- [ ] 5. Implement paper content validation
  - [ ] 5.1 Add paper file existence check
    - Verify paper file exists at locator path
    - Log error and print "File not found" message if missing
    - Mark paper as extraction_failed and return False
    - _Requirements: 11.1, 11.2, 11.9_
  
  - [ ] 5.2 Implement paper content length validation
    - Read paper content with UTF-8 encoding and errors="ignore"
    - Verify content contains at least 100 characters
    - Log warning and mark as extraction_failed if too short
    - Log actual character count at INFO level
    - _Requirements: 11.3, 11.4, 11.5, 11.6_
  
  - [ ] 5.3 Handle paper reading exceptions
    - Catch all exceptions during paper file read
    - Log error with file path and exception message
    - Print "Failed to read" message to console
    - Mark paper as extraction_failed and return False
    - _Requirements: 11.9, 14.9_

- [ ] 6. Implement user interaction display
  - [ ] 6.1 Implement display_extraction_instructions() function
    - Print visual separator line (70 equals characters)
    - Display paper title and source_id
    - Display saved prompt file path
    - Show instructions to open prompt with cat command
    - List 3 LLM options with URLs (ChatGPT, Claude, Gemini)
    - Show template save path with concrete example
    - Indicate ENTER to resume and Ctrl+C to skip
    - Print closing separator line
    - Ensure 80-character line width for terminal readability
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10_

- [ ] 7. Implement pause and resume mechanism
  - [ ] 7.1 Implement pause_for_user_input() function
    - Call Python input() with prompt text "Press ENTER when templates are saved (or Ctrl+C to skip)... "
    - Block execution until user presses ENTER
    - Print resume message when user presses ENTER
    - Return True on normal ENTER press
    - _Requirements: 5.1, 5.2, 5.3, 5.10_
  
  - [ ] 7.2 Add Ctrl+C interrupt handling
    - Catch KeyboardInterrupt exception during input()
    - Print message indicating user skipped the paper
    - Return False to indicate skip
    - Ensure process remains responsive to signals
    - _Requirements: 5.4, 5.5, 5.6, 5.7, 5.10_

- [ ] 8. Implement template detection system
  - [ ] 8.1 Implement template snapshot before pause
    - Scan templates directory using glob pattern "*.json"
    - Store set of template file paths before pause
    - Handle non-existent directory gracefully
    - _Requirements: 6.1, 6.2, 13.1_
  
  - [ ] 8.2 Implement detect_new_templates() function
    - Scan templates directory after user resume
    - Compare post-pause paths with pre-pause paths
    - Identify new template files
    - Print count and list each new filename
    - Log each detected file at INFO level
    - _Requirements: 5.8, 6.1, 6.2, 6.3, 13.2, 13.9_
  
  - [ ] 8.3 Implement validate_template_file() function
    - Check file size is greater than 0 bytes
    - Parse file content as JSON
    - Validate presence of required fields: template_id, skeleton, field_pairs, param_ranges
    - Check basic types (skeleton=string, field_pairs=list, param_ranges=dict)
    - Return tuple (is_valid, template_dict, error_message)
    - _Requirements: 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 12.1, 12.2, 12.3, 13.6, 13.7_
  
  - [ ] 8.4 Add template validation error handling
    - Print warning for JSON parsing failures
    - Print warning for missing required fields
    - Print warning for invalid field types
    - Skip invalid template but continue with others
    - Do not crash on validation failures
    - _Requirements: 6.5, 14.7_
  
  - [ ] 8.5 Implement template ID collision detection
    - Check if template_id already exists in Template_Registry
    - Print warning message with duplicate template_id
    - Skip loading duplicate template
    - Indicate existing template is preserved
    - Handle multiple new templates with same ID (load first only)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 13.5_

- [ ] 9. Implement status tracking system
  - [ ] 9.1 Implement update_paper_status() function
    - Update paper status field in registry
    - Record current UTC timestamp for status transitions
    - For pending_extraction: set prompt_generated_date and prompt_file
    - For extraction_skipped: set skipped_date
    - For consumed: set consumed_date and templates_created list
    - For extraction_failed: set read_date and increment extraction_attempts
    - Call _refresh_registry_stats() after status update
    - Save papers_registry immediately to disk
    - Log status update with source_id and new status
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 14.4_
  
  - [ ] 9.2 Implement _refresh_registry_stats() function
    - Count papers with status="consumed" exactly
    - Calculate remaining as total minus consumed
    - Include pending_extraction and extraction_skipped in remaining count
    - Update stats.total, stats.consumed, stats.remaining
    - Log statistics at DEBUG level
    - _Requirements: 3.10, 15.2, 15.3, 15.4_
  
  - [ ] 9.3 Ensure backwards compatibility with existing statuses
    - Continue recognizing existing values: unread, consumed, extraction_failed
    - Do not automatically migrate existing status values
    - Handle missing optional fields (default to None/empty)
    - Support displaying all status values in logs
    - _Requirements: 15.1, 15.2, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10_

- [ ] 10. Implement template hot-reload system
  - [ ] 10.1 Implement reload_template_registry() function
    - Scan templates/ directory for all *.json files
    - Parse each file and extract template_id
    - Update in-memory Template_Registry dictionary
    - Log updated template count at INFO level
    - Skip invalid files with warnings but continue
    - Preserve existing valid templates
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.8, 7.9, 7.10_
  
  - [ ] 10.2 Implement trigger_breadth_reset() function
    - Reset consecutive_no_active counter to zero
    - Log the reset action at INFO level
    - Ensure breadth phase runs in next round
    - _Requirements: 7.6, 7.7_
  
  - [ ] 10.3 Integrate reload into main mining loop
    - Call reload_template_registry() when fuel_one_paper_manual returns True
    - Call trigger_breadth_reset() after successful reload
    - Print message showing new template count
    - Update state template_count value
    - _Requirements: 7.1, 7.5, 7.8_

- [ ] 11. Rewrite fuel_one_paper_manual() function
  - [ ] 11.1 Replace broken implementation with new workflow
    - Get paper info from registry (title, type, locator)
    - Log manual extraction start with source_id, type, locator
    - Print manual extraction attempt message
    - _Requirements: 14.1, 14.10_
  
  - [ ] 11.2 Add paper validation sequence
    - Call paper file existence check
    - Call paper content reading and length validation
    - Handle validation failures by returning False
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ] 11.3 Add prompt generation sequence
    - Call load_skill_content() to get domain knowledge
    - Call load_field_catalog() to get available fields
    - Call generate_extraction_prompt() with all inputs
    - Handle missing dependencies errors
    - Print prompt generation status with character count
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.11, 1.12, 1.13_
  
  - [ ] 11.4 Add prompt save and status update sequence
    - Call save_extraction_prompt() with generated prompt
    - Handle file write failures
    - Call update_paper_status() with "pending_extraction" status
    - Pass prompt_file metadata
    - Log prompt save with file path and length
    - _Requirements: 2.1, 2.4, 2.5, 3.1, 3.2, 3.3, 14.3_
  
  - [ ] 11.5 Add user interaction sequence
    - Capture template snapshot before pause
    - Call display_extraction_instructions() with paper info and prompt path
    - Call pause_for_user_input() and capture return value
    - If False (Ctrl+C), update status to extraction_skipped and return False
    - If True (ENTER), proceed to template detection
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.4, 5.5, 5.6, 3.4, 3.5, 14.5_
  
  - [ ] 11.6 Add template detection sequence
    - Print resuming message
    - Call detect_new_templates() with before snapshot
    - If no new templates, print message and return False (stay pending_extraction)
    - If new templates found, print count and filenames
    - _Requirements: 5.8, 6.1, 6.2, 6.3, 14.6_
  
  - [ ] 11.7 Add template validation and loading sequence
    - For each new template file, call validate_template_file()
    - Check for template ID collisions
    - Skip invalid templates with warnings
    - Collect valid new template IDs
    - If no valid templates, return False
    - If valid templates found, update status to consumed with template IDs
    - Return True to signal successful extraction
    - _Requirements: 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 8.1, 8.2, 3.6, 3.7, 3.8_

- [ ] 12. Add comprehensive logging
  - [ ] 12.1 Add logging for manual extraction start
    - Log at INFO level with source_id, paper type, locator path
    - Include "depth-manual" or "manual" tag for filtering
    - _Requirements: 14.1, 14.10_
  
  - [ ] 12.2 Add logging for prompt generation and save
    - Log prompt character count at INFO level
    - Log file path and success status at INFO level
    - _Requirements: 14.2, 14.3, 14.10_
  
  - [ ] 12.3 Add logging for status updates
    - Log source_id and new status at INFO level for all status changes
    - _Requirements: 14.4, 14.10_
  
  - [ ] 12.4 Add logging for user skip action
    - Log source_id and "skipped by user" at INFO level
    - _Requirements: 14.5, 14.10_
  
  - [ ] 12.5 Add logging for template detection
    - Log source_id and count of new templates at INFO level
    - _Requirements: 14.6, 14.10_
  
  - [ ] 12.6 Add logging for validation failures
    - Log template filename and failure reason at WARNING level
    - _Requirements: 14.7, 14.10_
  
  - [ ] 12.7 Add logging for template reload
    - Log updated template count at INFO level
    - _Requirements: 14.8, 14.10_
  
  - [ ] 12.8 Add logging for file operation failures
    - Log file path and exception message at WARNING or ERROR level
    - _Requirements: 14.9, 14.10_

- [ ] 13. Checkpoint - Core functionality complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Write unit tests for helper functions
  - [ ]* 14.1 Write tests for format_field_catalog_for_prompt()
    - Test basic formatting with normal input
    - Test small categories show all fields (< 10)
    - Test large categories show truncation
    - Test category grouping and sorting
    - Test field count display
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.6, 9.10_
  
  - [ ]* 14.2 Write tests for load_example_templates()
    - Test loading with sufficient templates (>= 2)
    - Test handling insufficient templates (< 2)
    - Test skipping invalid JSON files
    - Test field_pairs truncation to 2 examples
    - _Requirements: 1.5, 12.1, 12.2_
  
  - [ ]* 14.3 Write tests for validate_template_file()
    - Test validation passes for valid template
    - Test validation fails for missing required fields
    - Test validation fails for empty file (0 bytes)
    - Test validation fails for invalid JSON
    - Test validation fails for template ID collision
    - Test validation fails for wrong field types
    - _Requirements: 6.5, 6.6, 6.7, 6.8, 8.1, 13.6_
  
  - [ ]* 14.4 Write tests for update_paper_status()
    - Test status update to pending_extraction with metadata
    - Test status update to extraction_skipped with timestamp
    - Test status update to consumed with templates_created list
    - Test status update to extraction_failed with attempts increment
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6_
  
  - [ ]* 14.5 Write tests for _refresh_registry_stats()
    - Test statistics computation from mixed statuses
    - Test consumed count only includes status="consumed"
    - Test remaining includes non-consumed statuses
    - Test new statuses treated as "not consumed"
    - _Requirements: 3.10, 15.2, 15.3, 15.4_
  
  - [ ]* 14.6 Write tests for generate_extraction_prompt()
    - Test prompt includes all required sections
    - Test prompt size reduction when exceeding 100k chars
    - Test handling missing SKILL.md (placeholder text)
    - Test handling missing field catalog (placeholder text)
    - _Requirements: 1.1, 1.2, 1.3, 1.14, 10.2, 10.3_
  
  - [ ]* 14.7 Write tests for paper content truncation
    - Test truncation at 10,000 characters
    - Test smart truncation format (first 8k + marker + last 2k)
    - Test no truncation for short papers
    - _Requirements: 1.10, 11.7_

- [ ] 15. Write integration tests
  - [ ]* 15.1 Write happy path integration test
    - Setup test environment with all dependencies
    - Mock input() to return immediately (ENTER)
    - Call fuel_one_paper_manual()
    - Verify prompt generated and saved
    - Simulate user creating valid template
    - Verify template detected and status updated to consumed
    - _Requirements: 1.1, 2.1, 5.1, 6.1, 3.6_
  
  - [ ]* 15.2 Write Ctrl+C skip integration test
    - Setup test environment
    - Mock input() to raise KeyboardInterrupt
    - Verify status updated to extraction_skipped
    - Verify function returns False
    - _Requirements: 5.4, 5.5, 5.6, 3.4_
  
  - [ ]* 15.3 Write no templates created integration test
    - Setup test environment
    - Mock input() to return (ENTER)
    - User creates no templates
    - Verify status remains pending_extraction
    - Verify function returns False
    - _Requirements: 6.11_
  
  - [ ]* 15.4 Write invalid template integration test
    - Setup test environment
    - Mock input() to return (ENTER)
    - User creates template with missing required fields
    - Verify validation fails with warning
    - Verify invalid template not loaded
    - Verify function continues without crashing
    - _Requirements: 6.5, 6.10, 14.7_
  
  - [ ]* 15.5 Write template reload integration test
    - Create new valid template during pause
    - Resume execution
    - Verify reload_template_registry() called
    - Verify new template appears in registry
    - Verify consecutive_no_active reset to 0
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

- [ ] 16. Write edge case tests
  - [ ]* 16.1 Write template ID collision test
    - Create template with ID matching existing template
    - Verify collision detected and warned
    - Verify existing template preserved
    - Verify new template skipped
    - _Requirements: 8.1, 8.2, 8.3, 13.5_
  
  - [ ]* 16.2 Write templates directory creation test
    - Start with no templates directory
    - Simulate directory creation during pause
    - Verify all files detected as new
    - _Requirements: 13.1, 13.2_
  
  - [ ]* 16.3 Write symbolic link template test
    - Create template file and symbolic link to it
    - Verify link followed and target processed
    - _Requirements: 13.8_
  
  - [ ]* 16.4 Write subdirectory templates test
    - Create templates/subdir/template.json
    - Verify subdirectory files ignored
    - _Requirements: 13.9_
  
  - [ ]* 16.5 Write missing dependencies test
    - Test with missing SKILL.md
    - Test with missing research_target.json
    - Test with < 2 template examples
    - Verify appropriate error handling for each
    - _Requirements: 1.11, 1.12, 1.13_

- [ ] 17. Final checkpoint - All tests passing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation of functionality
- Core implementation tasks (1-12) must be completed sequentially
- Testing tasks (14-16) can be executed in parallel after task 13
- The feature does not require property-based testing as it involves infrastructure, file I/O, and user interaction workflows
- All file operations use UTF-8 encoding with appropriate error handling
- Status transitions maintain backwards compatibility with existing papers_registry.json data

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4"] },
    { "id": 1, "tasks": ["2.1", "3.1", "5.1", "5.2"] },
    { "id": 2, "tasks": ["3.2", "3.3", "4.1", "5.3", "6.1"] },
    { "id": 3, "tasks": ["3.4", "4.2", "7.1", "8.1"] },
    { "id": 4, "tasks": ["7.2", "8.2", "8.3", "9.1"] },
    { "id": 5, "tasks": ["8.4", "8.5", "9.2", "10.1"] },
    { "id": 6, "tasks": ["9.3", "10.2"] },
    { "id": 7, "tasks": ["10.3", "11.1"] },
    { "id": 8, "tasks": ["11.2", "11.3"] },
    { "id": 9, "tasks": ["11.4", "11.5"] },
    { "id": 10, "tasks": ["11.6", "11.7"] },
    { "id": 11, "tasks": ["12.1", "12.2", "12.3", "12.4", "12.5", "12.6", "12.7", "12.8"] },
    { "id": 12, "tasks": ["14.1", "14.2", "14.3", "14.4", "14.5", "14.6", "14.7"] },
    { "id": 13, "tasks": ["15.1", "15.2", "15.3", "15.4", "15.5"] },
    { "id": 14, "tasks": ["16.1", "16.2", "16.3", "16.4", "16.5"] }
  ]
}
```
