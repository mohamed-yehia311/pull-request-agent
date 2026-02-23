# Hugging Face Hub Tagging Bot
*Note: This project is based on the [Hugging Face MCP Course - Unit 3: Webhooks & Agents](https://huggingface.co/learn/mcp-course/unit3_1/introduction).*

This project is an automated tagging agent for Hugging Face model repositories. It serves as a webhook listener built with FastAPI that automatically monitors model discussions. When a user asks a question or leaves a comment suggesting a machine learning tag (e.g., `#nlp`, `#vision`), this bot automatically extracts the tags, verifies them using an intelligent MCP agent, and creates a Pull Request on the Hugging Face Hub to add those tags to the model's `README.md` metadata!

## 🚀 Features
- **Webhook Integration**: Listens for `discussion.comment` events from Hugging Face Hub.
- **Smart Tag Extraction**: Recognizes both explicit tags (`tags: nlp, vision`) and implicit hashtag usage (`#question-answering`).
- **Automated PRs**: Uses the Hugging Face `HfApi` and an LLM-powered FastMCP Agent to automatically verify and create Pull Requests for new tags.

---

## 🛠️ Setup & Installation

### 1. Install Dependencies
You can install the required packages using `pip` or `uv`. This project requires Python 3.11+.

Using `pip`:
```bash
pip install .
```

Using `uv` (recommended for speed):
```bash
uv pip install -r pyproject.toml
```

### 2. Environment Variables
Create a `.env` file in the root of your project (you can copy `.env.example` if it exists) and add your Hugging Face credentials:

```dotenv
HF_TOKEN=your_huggingface_access_token_here
HF_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
WEBHOOK_SECRET=your_custom_secret_string
```

> **Note:** Your `HF_TOKEN` must have `write` permissions to the repositories you are monitoring to successfully create Pull Requests!

---

## 🏃 Running the Application

To run the FastAPI server, use `uvicorn`:

```bash
uvicorn src.api.server:app --reload --port 8000
```

The application will now be running locally at `http://127.0.0.1:8000`.

---

## 🌐 Setting up Webhooks & Ngrok

Hugging Face webhooks require a public, internet-accessible URL. Since your application is running locally on `localhost:8000`, you will need to expose it using **Ngrok**.

### 1. Start Ngrok
In a new terminal, run:
```bash
ngrok http 8000
```
This will generate a Forwarding URL (e.g., `https://1a2b3c4d.ngrok.app`).

### 2. Configure Hugging Face
1. Go to your Hugging Face account settings and navigate to the **Webhooks** section.
2. Click **Create a webhook**.
3. **Target Repositories**: Select the repositories you want to monitor (e.g., `MohmaedElnamir/test`).
4. **Webhook URL**: Enter your Ngrok URL followed by `/webhook` (e.g., `https://1a2b3c4d.ngrok.app/webhook`).
5. **Webhook Secret**: Enter the same secret string you put in your `.env` file under `WEBHOOK_SECRET`.
6. Save and enable the webhook!

### 3. Test It!
Go to the Hugging Face discussion tab on your monitored repository and leave a comment like:
> *"Does this model support #text-generation?"*

Watch your `uvicorn` console as the Tagging Bot processes the webhook and creates a PR on your repository!