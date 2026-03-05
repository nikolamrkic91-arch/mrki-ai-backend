use serde::{Deserialize, Serialize};
use zed_extension_api::{self as zed, Command, Extension, LanguageServerId, SlashCommand, SlashCommandArgumentCompletion, SlashCommandOutput, SlashCommandOutputSection, Worktree};

const MRLKI_LSP_SERVER_NAME: &str = "mrki-lsp";

/// Mrki Extension for Zed
pub struct MrkiExtension {
    /// Cached path to the language server
    language_server_path: Option<String>,
}

impl MrkiExtension {
    pub fn new() -> Self {
        Self {
            language_server_path: None,
        }
    }

    /// Get or find the language server path
    fn language_server_path(&mut self, worktree: &Worktree) -> Result<String, String> {
        if let Some(ref path) = self.language_server_path {
            return Ok(path.clone());
        }

        // Try to find mrki-lsp in PATH
        if let Ok(path) = worktree.which("mrki-lsp") {
            self.language_server_path = Some(path.clone());
            return Ok(path);
        }

        // Try common installation paths
        let common_paths = [
            "/usr/local/bin/mrki-lsp",
            "/usr/bin/mrki-lsp",
            "~/.local/bin/mrki-lsp",
            "~/.cargo/bin/mrki-lsp",
        ];

        for path in &common_paths {
            if std::path::Path::new(path).exists() {
                self.language_server_path = Some(path.to_string());
                return Ok(path.to_string());
            }
        }

        Err("mrki-lsp not found. Please install it: pip install mrki[lsp]".to_string())
    }

    /// Get language server arguments for a specific language
    fn language_server_args(&self, language: &str) -> Vec<String> {
        vec![
            "--language".to_string(),
            language.to_string(),
            "--stdio".to_string(),
        ]
    }
}

impl Extension for MrkiExtension {
    fn new() -> Self {
        Self::new()
    }

    /// Called when the extension is activated
    fn activate(&mut self, _worktree: &Worktree) -> Result<(), String> {
        zed::register_slash_command("mrki", SlashCommand {
            name: "mrki".to_string(),
            description: "Ask Mrki for help".to_string(),
            requires_argument: true,
        });

        zed::register_slash_command("mrki-explain", SlashCommand {
            name: "mrki-explain".to_string(),
            description: "Explain selected code with Mrki".to_string(),
            requires_argument: false,
        });

        zed::register_slash_command("mrki-test", SlashCommand {
            name: "mrki-test".to_string(),
            description: "Generate tests with Mrki".to_string(),
            requires_argument: false,
        });

        zed::register_slash_command("mrki-refactor", SlashCommand {
            name: "mrki-refactor".to_string(),
            description: "Refactor code with Mrki".to_string(),
            requires_argument: true,
        });

        Ok(())
    }

    /// Get the language server command
    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        worktree: &Worktree,
    ) -> Result<Command, String> {
        let path = self.language_server_path(worktree)?;
        
        Ok(Command {
            command: path,
            args: vec!["--stdio".to_string()],
            env: vec![],
        })
    }

    /// Get language server initialization options
    fn language_server_initialization_options(
        &mut self,
        _language_server_id: &LanguageServerId,
        _worktree: &Worktree,
    ) -> Result<Option<String>, String> {
        let options = serde_json::json!({
            "completion": {
                "enabled": true,
                "inlineEnabled": true,
            },
            "hover": {
                "enabled": true,
            },
            "codeActions": {
                "enabled": true,
            },
        });

        Ok(Some(options.to_string()))
    }

    /// Execute a slash command
    fn run_slash_command(
        &mut self,
        command: &SlashCommand,
        args: &[String],
        _worktree: Option<&Worktree>,
    ) -> Result<SlashCommandOutput, String> {
        match command.name.as_str() {
            "mrki" => self.handle_mrki_command(args),
            "mrki-explain" => self.handle_explain_command(),
            "mrki-test" => self.handle_test_command(),
            "mrki-refactor" => self.handle_refactor_command(args),
            _ => Err(format!("Unknown command: {}", command.name)),
        }
    }

    /// Get completions for slash command arguments
    fn complete_slash_command_argument(
        &mut self,
        command: &SlashCommand,
        args: &[String],
    ) -> Result<Vec<SlashCommandArgumentCompletion>, String> {
        match command.name.as_str() {
            "mrki" => Ok(vec![
                SlashCommandArgumentCompletion {
                    label: "explain".to_string(),
                    description: Some("Explain code".to_string()),
                    new_text: "explain ".to_string(),
                    run_command: false,
                },
                SlashCommandArgumentCompletion {
                    label: "test".to_string(),
                    description: Some("Generate tests".to_string()),
                    new_text: "test ".to_string(),
                    run_command: false,
                },
                SlashCommandArgumentCompletion {
                    label: "refactor".to_string(),
                    description: Some("Refactor code".to_string()),
                    new_text: "refactor ".to_string(),
                    run_command: false,
                },
            ]),
            "mrki-refactor" => Ok(vec![
                SlashCommandArgumentCompletion {
                    label: "simplify".to_string(),
                    description: Some("Simplify code".to_string()),
                    new_text: "simplify".to_string(),
                    run_command: true,
                },
                SlashCommandArgumentCompletion {
                    label: "optimize".to_string(),
                    description: Some("Optimize performance".to_string()),
                    new_text: "optimize".to_string(),
                    run_command: true,
                },
                SlashCommandArgumentCompletion {
                    label: "modernize".to_string(),
                    description: Some("Use modern patterns".to_string()),
                    new_text: "modernize".to_string(),
                    run_command: true,
                },
            ]),
            _ => Ok(vec![]),
        }
    }
}

impl MrkiExtension {
    fn handle_mrki_command(&self, args: &[String]) -> Result<SlashCommandOutput, String> {
        let query = args.join(" ");
        
        // In a real implementation, this would call the Mrki backend
        let response = format!("**Mrki**: I'll help you with: _{}_\n\nProcessing your request...", query);

        Ok(SlashCommandOutput {
            text: response,
            sections: vec![SlashCommandOutputSection {
                range: (0, response.len()),
                label: "Mrki Response".to_string(),
            }],
            run_commands_in_text: false,
        })
    }

    fn handle_explain_command(&self) -> Result<SlashCommandOutput, String> {
        let text = "**Mrki**: I'll explain the selected code.\n\nPlease select the code you want explained, and I'll provide a detailed breakdown of what it does.";

        Ok(SlashCommandOutput {
            text: text.to_string(),
            sections: vec![SlashCommandOutputSection {
                range: (0, text.len()),
                label: "Mrki Explain".to_string(),
            }],
            run_commands_in_text: false,
        })
    }

    fn handle_test_command(&self) -> Result<SlashCommandOutput, String> {
        let text = "**Mrki**: I'll generate tests for the selected code.\n\nPlease select the function or class you want tests for.";

        Ok(SlashCommandOutput {
            text: text.to_string(),
            sections: vec![SlashCommandOutputSection {
                range: (0, text.len()),
                label: "Mrki Test Generator".to_string(),
            }],
            run_commands_in_text: false,
        })
    }

    fn handle_refactor_command(&self, args: &[String]) -> Result<SlashCommandOutput, String> {
        let refactor_type = args.get(0).map(|s| s.as_str()).unwrap_or("general");
        
        let text = format!(
            "**Mrki**: I'll refactor the selected code ({}).\n\nPlease select the code you want refactored.",
            refactor_type
        );

        Ok(SlashCommandOutput {
            text: text.clone(),
            sections: vec![SlashCommandOutputSection {
                range: (0, text.len()),
                label: "Mrki Refactor".to_string(),
            }],
            run_commands_in_text: false,
        })
    }
}

zed::register_extension!(MrkiExtension);
