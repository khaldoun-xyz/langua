# app.py
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

from evaluation_utils.evaluate import evaluate_last_conversation
from utils.config import Config, initialize_groq_client
from utils.conversation_utils import ConversationManager
from utils.database_utils import fetch_all_users, fetch_progress_data
from utils.learning_themes import LEARNING_THEMES

client = initialize_groq_client()
MODEL = Config.MODEL
app = Flask(__name__, template_folder="templates")
socketio = SocketIO(app)

conversations = {}
conversation_manager = ConversationManager()


@app.route("/start-evaluation", methods=["POST"])
def start_evaluation():
    data = request.json
    username, language, theme = data["username"], data["language"], data["theme"]
    conversation_data = conversation_manager.initialize_conversation(
        language, theme, username
    )
    conversations[username] = conversation_data
    return jsonify({"response": conversation_data["history"][0]["content"]})


@app.route("/restart-conversation", methods=["POST"])
def restart_conversation():
    data = request.json
    username, language, theme = data["username"], data["language"], data["theme"]
    conversation_data = conversation_manager.initialize_conversation(
        language, theme, username
    )
    conversations[username] = conversation_data
    return jsonify({"response": conversation_data["history"][0]["content"]})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    username, user_message = data["username"], data["message"]
    if username not in conversations:
        return jsonify({"error": "No active conversation found."}), 404

    response = conversation_manager.process_user_message(
        conversations, username, user_message
    )
    if isinstance(response, dict) and "error" in response:
        return jsonify(response), 500
    return jsonify({"response": response})


@app.route("/end-conversation", methods=["POST"])
def end_conversation_route():
    username = request.json["username"]
    if username not in conversations:
        return jsonify({"error": "No active conversation found."}), 404

    summary = conversation_manager.log_end_conversation(conversations, username)
    return jsonify(summary)


@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.json
    username = data.get("username")
    if username not in conversations:
        return jsonify({"error": "No active conversation found."}), 404

    result = evaluate_last_conversation(username, conversations[username]["language"])
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 400
    return jsonify({"evaluation": result})


@app.route("/fetch-progress", methods=["POST"])
def fetch_progress():
    try:
        data = request.json
        username = data.get("username")
        sort_order = data.get("sort_order", "asc")
        language_filter = data.get("language", "all")
        theme_filter = data.get("theme", "all")

        progress = fetch_progress_data(
            username=username,
            sort_order=sort_order,
            language_filter=language_filter,
            theme_filter=theme_filter,
        )

        if progress is None:
            return (
                jsonify({"error": "An error occurred while fetching progress data"}),
                500,
            )

        if not progress:
            return (
                jsonify(
                    {
                        "progress": [],
                        "message": "No data found for the selected filters",
                    }
                ),
                200,
            )

        return jsonify({"progress": progress}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/track_progress")
def track_progress():
    return render_template(
        "lugha/track_progress.html", learning_themes=LEARNING_THEMES.keys()
    )


@app.route("/chat-interface")
def chat_interface():
    username = request.args.get("username")
    language = request.args.get("language")
    theme = request.args.get("theme")
    return render_template(
        "lugha/chat_interface.html",
        username=username,
        language=language,
        theme=theme,
        learning_themes=LEARNING_THEMES.keys(),
    )


@app.route("/")
def welcome():
    return render_template("lugha/welcome.html", learning_themes=LEARNING_THEMES.keys())


@app.route("/admin")
def admin_page():
    users = fetch_all_users()
    return render_template("lugha/admin.html", users=users)


@app.route("/api/conversations/<username>")
def get_conversations(username):
    conversations_data = fetch_progress_data(username)
    return jsonify(conversations_data)


@app.route("/api/users")
def get_users():
    users = fetch_all_users()
    return jsonify(users)


if __name__ == "__main__":
    app.run(debug=True)
