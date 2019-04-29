import requests

class QuestionGenerator:

    def generate_questions(self, text, entities):
        
        questions = []
        
        if len(text.split(" ")) > 3:
            for answer in entities:
                payload = (
                    ("context", text),
                    ("answer", answer)
                )
                question = requests.get("http://localhost:5004/api/generate", params=payload).text.replace(" <\Sent>", "").replace(" &lt;/Sent&gt;", "")

                questions.append({
                    "question": question,
                    "answer": answer
                })

        return questions