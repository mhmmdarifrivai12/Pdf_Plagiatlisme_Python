from flask import Flask, render_template, request
import os
import fitz  # PyMuPDF
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Folder untuk menyimpan upload
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fungsi untuk melakukan OCR pada file PDF
def ocr_pdf(filepath):
    try:
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return str(e)

# Fungsi untuk mendeteksi plagiarisme antara dua teks
def detect_plagiarism(text1, text2):
    vectorizer = CountVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    similarity = cosine_similarity(vectors)[0,1]
    return similarity

# Fungsi untuk mencari kalimat yang sama antara dua teks
def find_duplicate_sentences(text1, text2):
    sentences1 = text1.split('.')
    sentences2 = text2.split('.')
    
    plagiarized_sentences = []
    for sentence1 in sentences1:
        if sentence1.strip() == '':
            continue
        for sentence2 in sentences2:
            if sentence2.strip() == '':
                continue
            if sentence1.strip() == sentence2.strip():
                plagiarized_sentences.append(sentence1.strip())

    return '. '.join(plagiarized_sentences)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file1' not in request.files or 'file2' not in request.files:
        return render_template('index.html', error='Please upload both files.')

    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1.filename == '' or file2.filename == '':
        return render_template('index.html', error='Please select both files.')

    if file1 and file2:
        filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
        file1.save(filepath1)
        file2.save(filepath2)

        text1 = ocr_pdf(filepath1)
        text2 = ocr_pdf(filepath2)

        similarity = detect_plagiarism(text1, text2)
        plagiarism_text = "Plagiarism detected: {:.2%} similar.".format(similarity)

        if similarity >= 0.5:
            plagiarized_sentences = find_duplicate_sentences(text1, text2)
        else:
            plagiarized_sentences = None

        return render_template('index.html', filename1=file1.filename, filename2=file2.filename, plagiarism_text=plagiarism_text, status_file1="Uploaded", status_file2="Uploaded", plagiarized_sentences=plagiarized_sentences, text1=text1, text2=text2)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
