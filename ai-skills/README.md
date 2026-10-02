# Opcoda coding guides

Opcoda reads these Markdown files when it generates a relevant website. Edit them to change its design and coding guidance; the next request picks up the changes after the server has loaded the skill reader. No model training command is needed for Markdown edits.

Files are selected by words in the request. Keep instructions short and concrete, with examples that show the result you want. Explicit user requests always win. This folder is generation guidance, not model weight training or permanent memory of chats.

To improve it from examples, add a **reviewed** Markdown guide with a descriptive filename, a short `Keywords:` line, and a specific good pattern. Do not save a model output as a good example until you have checked it in desktop and mobile previews.

For actual weight training, examples would need to be collected into a separate dataset and used in a fine-tuning run. The live Ollama model is not fine-tuned by these files.
