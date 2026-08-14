# Requirements Document

## Introduction

The alpha mining system is a semi-automated research tool that generates quantitative trading alpha factors for the WorldQuant BRAIN platform. The system operates in a breadth-depth cycle: the breadth phase expands existing template libraries to generate and test new alpha candidates, while the depth phase extracts new templates from research papers to expand the template pool.

This feature implements a working manual extraction workflow for the depth phase. Currently, the `--depth-backend manual` mode is broken—it reads paper content but immediately marks papers as "extraction_failed" without generating extraction prompts, pausing for user input, or providing any mechanism for users to contribute templates. This feature will enable human-in-the-loop template extraction using external LLMs (ChatGPT, Claude, Gemini, or local models) without requiring API keys, providing full transparency and user control over the extraction process.

## Glossary

- **Alpha_Factor**: A quantitative signal that predicts stock returns in the WorldQuant BRAIN platform
- **Template**: A parameterized skeleton expression that generates multiple alpha candidate variations through parameter expansion
- **Template_Registry**: The in-memory dictionary of all loaded template definitions keyed by template_id
- **Breadth_Phase**: Mining loop phase that expands existing templates into alpha candidates, simulates them, and submits qualifying alphas
- **Depth_Phase**: Mining loop phase that extracts new templates from unread research papers to expand the template pool
- **Extraction_Prompt**: An LLM-ready text file combining paper content, domain knowledge (SKILL.md), field catalog, and instructions for extracting alpha templates
- **Mining_Loop**: The main script (mining_loop.py) that orchestrates breadth-depth cycles until termination conditions are met
- **Papers_Registry**: A JSON file (papers_registry.json) tracking all research papers, their extraction status, and metadata
- **Field_Catalog**: The JSON file listing all available data fields for the target pool (e.g., references/wq_glb_topdiv3000_delay1_data_fields.json)
- **SKILL_Content**: The domain knowledge document (SKILL.md) containing WorldQuant alpha design patterns, operators, and best practices
- **Paper_Status**: The extraction status of a research paper (unread, pending_extraction, consumed, extraction_failed, extraction_skipped)
- **Template_File**: A JSON file in templates/ directory containing a template definition with required fields: template_id, skeleton, field_pairs, param_ranges
- **Pause_Mechanism**: The user interaction workflow that halts Mining_Loop execution until the user presses ENTER

## Requirements

### Requirement 1: Generate LLM-Ready Extraction Prompt

**User Story:** As a quantitative researcher, I want the system to generate a comprehensive extraction prompt, so that I can use any LLM to extract high-quality alpha templates from research papers.

#### Acceptance Criteria

1. WHEN the Depth_Phase selects an unread paper, THE Mining_Loop SHALL generate an Extraction_Prompt containing the complete text content from the paper file limited to 10000 characters
2. THE Extraction_Prompt SHALL include SKILL knowledge content extracted from sections 4, 6, and 10 of the SKILL.md file
3. THE Extraction_Prompt SHALL include a formatted Field_Catalog summary containing 50 to 100 fields selected by highest alphaCount per category and grouped by category name
4. IF a category in the Field_Catalog contains fewer than 10 fields total, THEN THE Mining_Loop SHALL include all available fields from that category
5. THE Extraction_Prompt SHALL include 2 to 3 example Template_Files selected from the templates directory, prioritizing templates with highest pass_rate from lessons
6. THE Extraction_Prompt SHALL specify the target configuration containing region, universe, delay, neutralizations array, and excluded_dataset_ids from config/research_target.json
7. THE Extraction_Prompt SHALL include explicit instructions containing the required template schema fields (template_id, description, skeleton, field_pairs, param_ranges, default_settings, hypothesis, source) and requesting 1 to 5 template extractions in valid JSON array format
8. THE Extraction_Prompt SHALL include instructions specifying that the LLM must use ONLY fields present in the provided Field_Catalog
9. THE Extraction_Prompt SHALL include instructions specifying that the LLM must output ONLY a valid JSON array with no markdown code fences, explanatory text, or preamble
10. WHEN paper content exceeds 10000 characters, THE Mining_Loop SHALL truncate to first 8000 characters plus the text "[... TRUNCATED ...]" plus last 2000 characters
11. IF the paper file cannot be read due to missing file or encoding errors, THEN THE Mining_Loop SHALL generate an error response indicating paper read failure with the specific error reason
12. IF any required file (SKILL.md, config/research_target.json) is missing, THEN THE Mining_Loop SHALL generate an error response indicating missing dependency with the file path
13. IF the templates directory contains fewer than 2 valid JSON template files, THEN THE Mining_Loop SHALL generate an error response indicating insufficient template examples with the count found
14. IF the total assembled prompt exceeds 100000 characters, THEN THE Mining_Loop SHALL reduce Field_Catalog size to 50 fields minimum and reduce template examples to 2 minimum to fit within limit

### Requirement 2: Save Extraction Prompt to File

**User Story:** As a quantitative researcher, I want the extraction prompt saved to a predictable file location, so that I can easily access and copy it to my LLM interface.

#### Acceptance Criteria

1. THE Mining_Loop SHALL save the Extraction_Prompt to file path `._fuel_prompt.txt` in the workspace root directory
2. THE Mining_Loop SHALL use UTF-8 encoding when writing the Extraction_Prompt file
3. WHEN the Extraction_Prompt file already exists, THE Mining_Loop SHALL overwrite it with new content
4. THE Mining_Loop SHALL log the saved file path and prompt character count at INFO level
5. IF the Extraction_Prompt file write operation fails, THEN THE Mining_Loop SHALL log the error and mark the paper status as extraction_failed

### Requirement 3: Update Paper Status Tracking

**User Story:** As a system operator, I want papers to have accurate status tracking throughout the extraction workflow, so that I can monitor progress and retry failed extractions.

#### Acceptance Criteria

1. WHEN an Extraction_Prompt is successfully generated and saved, THE Mining_Loop SHALL set Paper_Status to "pending_extraction"
2. WHEN Paper_Status is set to pending_extraction, THE Mining_Loop SHALL record the current UTC timestamp in the prompt_generated_date field
3. WHEN Paper_Status is set to pending_extraction, THE Mining_Loop SHALL record the prompt file path in the prompt_file field
4. WHEN the user presses Ctrl+C during the Pause_Mechanism, THE Mining_Loop SHALL set Paper_Status to "extraction_skipped"
5. WHEN Paper_Status is set to extraction_skipped, THE Mining_Loop SHALL record the current UTC timestamp in the skipped_date field
6. WHEN new Template_Files are detected after user resume, THE Mining_Loop SHALL set Paper_Status to "consumed"
7. WHEN Paper_Status is set to consumed, THE Mining_Loop SHALL record the current UTC timestamp in the consumed_date field
8. WHEN Paper_Status is set to consumed, THE Mining_Loop SHALL record template_ids of new templates in the templates_created field
9. WHEN Paper_Status is updated, THE Mining_Loop SHALL immediately save the Papers_Registry to disk
10. WHEN Papers_Registry is saved, THE Mining_Loop SHALL recompute stats.consumed and stats.remaining from source statuses

### Requirement 4: Display User Instructions

**User Story:** As a quantitative researcher, I want clear step-by-step instructions displayed when the system pauses, so that I know exactly how to extract templates and resume the mining loop.

#### Acceptance Criteria

1. WHEN the Pause_Mechanism is triggered, THE Mining_Loop SHALL print a visual separator line of 70 equals characters
2. THE Mining_Loop SHALL display the paper title and source_id
3. THE Mining_Loop SHALL display the saved Extraction_Prompt file path
4. THE Mining_Loop SHALL display instructions to open the prompt file with a cat command example
5. THE Mining_Loop SHALL display instructions listing three LLM options: ChatGPT, Claude, and Gemini with their URLs
6. THE Mining_Loop SHALL display instructions to save templates as templates/<template_id>.json with a concrete example filename
7. THE Mining_Loop SHALL display instructions to press ENTER to resume after saving templates
8. THE Mining_Loop SHALL indicate that Ctrl+C can be used to skip the current paper
9. THE Mining_Loop SHALL display a closing visual separator line
10. THE instructions SHALL fit within 80 character line width for terminal readability

### Requirement 5: Implement Pause and Resume Mechanism

**User Story:** As a quantitative researcher, I want the mining loop to pause and wait for my input, so that I have time to extract templates using an external LLM without rushing.

#### Acceptance Criteria

1. WHEN instructions are displayed, THE Mining_Loop SHALL call the Python input() function with prompt text "Press ENTER when templates are saved (or Ctrl+C to skip)... "
2. THE input() call SHALL block Mining_Loop execution until the user presses ENTER
3. WHEN the user presses ENTER, THE Mining_Loop SHALL print a resume message indicating template scanning has started
4. WHEN the user presses Ctrl+C during input(), THE Mining_Loop SHALL catch the KeyboardInterrupt exception
5. WHEN KeyboardInterrupt is caught, THE Mining_Loop SHALL print a message indicating the user skipped the paper
6. WHEN KeyboardInterrupt is caught, THE Mining_Loop SHALL update Paper_Status to extraction_skipped
7. WHEN KeyboardInterrupt is caught, THE Mining_Loop SHALL return False from the fuel_one_paper_manual function
8. WHEN the user presses ENTER, THE Mining_Loop SHALL scan the templates directory for new Template_Files
9. THE Mining_Loop SHALL compare template files before pause with template files after resume using file path comparison
10. FOR ALL Pause_Mechanism invocations, the system SHALL remain responsive to process signals and not enter an uninterruptible wait state

### Requirement 6: Detect and Validate New Template Files

**User Story:** As a system operator, I want the system to detect newly created template files and validate their structure, so that only valid templates are loaded into the Template_Registry.

#### Acceptance Criteria

1. WHEN the user resumes from Pause_Mechanism, THE Mining_Loop SHALL scan the templates directory using glob pattern "*.json"
2. THE Mining_Loop SHALL identify new Template_Files by comparing current template file paths with pre-pause template file paths
3. WHEN new Template_Files are detected, THE Mining_Loop SHALL print the count and list each filename
4. THE Mining_Loop SHALL read each new Template_File and parse it as JSON
5. IF JSON parsing fails for a Template_File, THEN THE Mining_Loop SHALL print a warning message and skip that file
6. THE Mining_Loop SHALL validate that each parsed template contains required field "template_id"
7. THE Mining_Loop SHALL validate that each parsed template contains required field "skeleton"
8. THE Mining_Loop SHALL validate that each parsed template contains required field "field_pairs"
9. THE Mining_Loop SHALL validate that each parsed template contains required field "param_ranges"
10. WHEN validation passes for new templates, THE Mining_Loop SHALL return True from fuel_one_paper_manual function
11. WHEN no new valid templates are detected, THE Mining_Loop SHALL return False from fuel_one_paper_manual function

### Requirement 7: Hot-Reload Template Registry

**User Story:** As a system operator, I want newly created templates to be immediately available for the next breadth phase, so that the mining loop can utilize them without restarting.

#### Acceptance Criteria

1. WHEN fuel_one_paper_manual returns True, THE Mining_Loop SHALL trigger template registry reload
2. THE reload process SHALL scan the templates directory and read all JSON files matching pattern "*.json"
3. THE reload process SHALL parse each Template_File and extract the template_id field
4. THE reload process SHALL update the in-memory Template_Registry dictionary with all parsed templates keyed by template_id
5. THE reload process SHALL log the updated template count at INFO level
6. WHEN template registry reload completes, THE Mining_Loop SHALL reset the consecutive_no_active counter to zero
7. THE consecutive_no_active reset SHALL ensure the Breadth_Phase runs in the next round even if it would otherwise be skipped
8. THE reload process SHALL print a message indicating template registry was updated and show the new template count
9. IF template reload fails for any file, THE Mining_Loop SHALL log a warning and continue with successfully loaded templates
10. FOR ALL template reloads, existing valid templates SHALL be preserved and not removed from the Template_Registry

### Requirement 8: Handle Template ID Collisions

**User Story:** As a system operator, I want the system to detect and warn about duplicate template IDs, so that I can avoid accidentally overwriting existing templates.

#### Acceptance Criteria

1. WHEN validating a new Template_File, THE Mining_Loop SHALL check if the template_id already exists in the Template_Registry
2. IF a template_id collision is detected, THEN THE Mining_Loop SHALL print a warning message including the duplicate template_id
3. WHEN a template_id collision occurs, THE Mining_Loop SHALL skip loading that template into the Template_Registry
4. THE collision warning message SHALL indicate that the existing template is being preserved
5. WHEN multiple new templates have the same template_id, THE Mining_Loop SHALL load only the first encountered instance

### Requirement 9: Format Field Catalog for Prompt

**User Story:** As a quantitative researcher receiving an extraction prompt, I want the field catalog to be concisely summarized by category, so that I can quickly identify relevant fields without reading thousands of entries.

#### Acceptance Criteria

1. THE Field_Catalog formatter SHALL group fields by their category attribute
2. THE formatter SHALL display up to 100 total fields across all categories
3. THE formatter SHALL show up to 10 fields per category as representative examples
4. THE formatter SHALL display the total available field count at the top of the output
5. THE formatter SHALL sort categories alphabetically for consistent presentation
6. WHEN a category has more than 10 fields, THE formatter SHALL add an ellipsis line showing remaining count
7. THE formatter SHALL display each field name in a bulleted list format
8. THE formatter SHALL use markdown bold formatting for category headers
9. WHEN the Field_Catalog file does not exist, THE formatter SHALL return a placeholder message indicating the catalog is unavailable
10. FOR ALL formatting operations, category names SHALL be displayed in uppercase for visual distinction

### Requirement 10: Load Domain Knowledge Content

**User Story:** As a quantitative researcher, I want the extraction prompt to include complete domain knowledge, so that the LLM can generate templates consistent with WorldQuant BRAIN patterns and operator syntax.

#### Acceptance Criteria

1. THE Mining_Loop SHALL read the complete SKILL.md file content using UTF-8 encoding
2. WHEN SKILL.md file exists, THE Mining_Loop SHALL include its entire content in the Extraction_Prompt without truncation
3. WHEN SKILL.md file does not exist, THE Mining_Loop SHALL include the placeholder text "(SKILL.md not found)" in the Extraction_Prompt
4. THE SKILL_Content SHALL be inserted into the Extraction_Prompt in a clearly labeled section titled "Domain Knowledge"
5. IF reading SKILL.md fails due to encoding errors, THE Mining_Loop SHALL log a warning and use an empty string

### Requirement 11: Validate Paper Content Availability

**User Story:** As a system operator, I want the system to verify that paper content is readable and sufficiently long, so that extraction prompts are not generated from empty or corrupt files.

#### Acceptance Criteria

1. WHEN attempting manual extraction, THE Mining_Loop SHALL verify the paper file exists at the specified locator path
2. IF the paper file does not exist, THEN THE Mining_Loop SHALL log an error, print a "File not found" message, and return False
3. THE Mining_Loop SHALL read paper content using UTF-8 encoding with errors set to "ignore" mode
4. WHEN paper content is successfully read, THE Mining_Loop SHALL verify it contains at least 100 characters
5. IF paper content is shorter than 100 characters, THEN THE Mining_Loop SHALL log a warning, mark Paper_Status as extraction_failed, and return False
6. THE Mining_Loop SHALL log the actual character count of successfully read paper content at INFO level
7. WHEN paper type is PDF, THE Mining_Loop SHALL extract text content limited to 10000 characters
8. WHEN paper type is markdown, THE Mining_Loop SHALL read text content limited to 10000 characters
9. IF reading paper content raises an exception, THEN THE Mining_Loop SHALL log the error, print a "Failed to read" message, and return False
10. FOR ALL supported paper types (pdf, markdown), the same character limits and validation rules SHALL apply

### Requirement 12: Preserve Parser Round-Trip Property

**User Story:** As a quality engineer, I want template files to be parsable and re-serializable without loss, so that template integrity is maintained through read-write cycles.

#### Acceptance Criteria

1. WHEN THE Mining_Loop reads a Template_File and parses it as JSON, the parsed template SHALL be a valid Python dictionary
2. WHEN the parsed template dictionary is serialized back to JSON using json.dumps, the result SHALL be valid JSON
3. FOR ALL Template_Files in the templates directory, reading with json.loads followed by writing with json.dumps SHALL preserve all required fields
4. THE round-trip property SHALL hold for fields: template_id, description, skeleton, field_pairs, param_ranges, default_settings, hypothesis
5. WHEN a Template_File contains Unicode characters, THE round-trip SHALL preserve them using ensure_ascii=False setting

### Requirement 13: Handle Edge Cases in Template Detection

**User Story:** As a system operator, I want the system to handle edge cases gracefully during template detection, so that the mining loop remains robust under various user actions.

#### Acceptance Criteria

1. WHEN the templates directory does not exist before pause, THE Mining_Loop SHALL handle the exception and treat it as zero templates present
2. WHEN the templates directory is created during pause, THE Mining_Loop SHALL detect all Template_Files as new
3. WHEN a Template_File is deleted during pause, THE Mining_Loop SHALL not report it as a new template
4. WHEN a Template_File is modified but not renamed during pause, THE Mining_Loop SHALL not detect it as new
5. WHEN multiple Template_Files with identical template_ids are created during pause, THE Mining_Loop SHALL load only the first valid one and warn about duplicates
6. WHEN a Template_File is an empty file (0 bytes), THE Mining_Loop SHALL skip it with a warning
7. WHEN a Template_File contains non-JSON content, THE Mining_Loop SHALL skip it with a parsing error warning
8. WHEN a Template_File is a symbolic link, THE Mining_Loop SHALL follow the link and process the target file
9. WHEN the user creates a subdirectory in templates/ during pause, THE Mining_Loop SHALL ignore files in subdirectories
10. FOR ALL edge cases, THE Mining_Loop SHALL continue execution and not raise unhandled exceptions

### Requirement 14: Log Comprehensive Diagnostic Information

**User Story:** As a system maintainer, I want comprehensive logging throughout the manual extraction workflow, so that I can diagnose issues and audit system behavior.

#### Acceptance Criteria

1. WHEN manual extraction starts, THE Mining_Loop SHALL log source_id, paper type, and locator path at INFO level
2. WHEN an Extraction_Prompt is generated, THE Mining_Loop SHALL log the prompt character count at INFO level
3. WHEN an Extraction_Prompt is saved, THE Mining_Loop SHALL log the file path and success status at INFO level
4. WHEN Paper_Status is updated, THE Mining_Loop SHALL log the source_id and new status at INFO level
5. WHEN the user skips extraction with Ctrl+C, THE Mining_Loop SHALL log source_id and "skipped by user" at INFO level
6. WHEN new templates are detected, THE Mining_Loop SHALL log source_id and count of new templates at INFO level
7. WHEN template validation fails, THE Mining_Loop SHALL log the template filename and failure reason at WARNING level
8. WHEN template registry is reloaded, THE Mining_Loop SHALL log the updated template count at INFO level
9. WHEN file operations fail, THE Mining_Loop SHALL log the file path and exception message at WARNING or ERROR level
10. FOR ALL log messages related to manual extraction, the message SHALL include "depth-manual" or "manual" tag for filtering

### Requirement 15: Maintain Backwards Compatibility with Existing Status Values

**User Story:** As a system operator with existing papers_registry.json data, I want new status values to coexist with existing ones, so that previously processed papers are not affected by the upgrade.

#### Acceptance Criteria

1. THE Mining_Loop SHALL continue to recognize existing Paper_Status values: unread, consumed, extraction_failed
2. WHEN computing papers_registry statistics, THE Mining_Loop SHALL count consumed papers using status="consumed" exactly
3. WHEN computing remaining papers, THE Mining_Loop SHALL count all papers where status is NOT "consumed"
4. THE new status values pending_extraction and extraction_skipped SHALL be treated as "not consumed" in statistics
5. WHEN loading an existing papers_registry.json without new status values, THE Mining_Loop SHALL not raise errors or warnings
6. WHEN a paper with status pending_extraction is encountered in a future depth phase, THE Mining_Loop SHALL allow re-attempting extraction
7. WHEN a paper with status extraction_skipped is encountered in a future depth phase, THE Mining_Loop SHALL allow re-attempting extraction
8. THE Mining_Loop SHALL NOT automatically migrate existing status values to new status values
9. WHEN displaying paper status in logs or console output, THE Mining_Loop SHALL handle all status values with appropriate formatting
10. FOR ALL papers_registry.json read operations, missing optional fields (prompt_generated_date, skipped_date, templates_created) SHALL default to None or empty values

