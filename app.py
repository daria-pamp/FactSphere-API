from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask("FactSphere")

# Настраиваем базу данных
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Модель базы данных
class TextAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(500), nullable=True)


# Создаём таблицы в базе данных (делаем 1 раз)
with app.app_context():
    db.create_all()


# Главная страница
@app.route("/")
def hello():
    return "Hello from FactSphere!"


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()

    text = data.get("text", "")
    url = data.get("url", "")

    # Анализ текста
    word_count = len(text.split())
    char_count = len(text)
    contains_ai = any(word.lower() in text.lower() for word in ["ai", "flask", "python", "ml", "data"])

    # Анализ тональности
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(text)["compound"]

    if sentiment_score >= 0.05:
        sentiment = "positive"
    elif sentiment_score <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Сохраняем в базу данных
    new_record = TextAnalysis(text=text, url=url)
    db.session.add(new_record)
    db.session.commit()

    return jsonify({
        "received_text": text,
        "received_url": url,
        "status": "Saved to DB",
        "word_count": word_count,
        "char_count": char_count,
        "contains_ai": contains_ai,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score
    })


@app.route("/records", methods=["GET"])
def get_records():
    query = request.args.get("query", "")  # Получаем параметр из URL (по умолчанию пустая строка)

    if query:
        records = TextAnalysis.query.filter(TextAnalysis.text.contains(query)).all()
    else:
        records = TextAnalysis.query.all()

    return jsonify([
        {"id": record.id, "text": record.text, "url": record.url}
        for record in records
    ])


@app.route("/history", methods=["GET"])
def get_history():
    records = TextAnalysis.query.all()

    return jsonify([
        {
            "id": record.id,
            "text": record.text,
            "url": record.url
        }
        for record in records
    ])


@app.route("/delete/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    record = TextAnalysis.query.get(record_id)

    if not record:
        return jsonify({"error": "Record not found"}), 404

    db.session.delete(record)
    db.session.commit()

    return jsonify({"message": f"Record {record_id} deleted successfully"})

@app.route("/clear", methods=["DELETE"])
def clear_database():
    try:
        num_deleted = db.session.query(TextAnalysis).delete()  # Удаляем все записи
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} records successfully"})
    except Exception as e:
        db.session.rollback()  # Если ошибка, откатываем изменения
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
