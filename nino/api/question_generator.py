import subprocess

class QuestionGenerator:

    def generate_questions(self, text):
        out = subprocess.Popen(['./nino/question_generation/get_qnas', text.encode('utf-8')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()

        res_lines = stdout.decode("utf-8").strip("\n").split("\n")
        res = []
        
        if not res_lines[0]:
            return res
        
        for line in res_lines:
            question, answer, score = line.split("\t")
            res.append({
                "question": question,
                "answer": answer,
                "score": score
            })
        return res