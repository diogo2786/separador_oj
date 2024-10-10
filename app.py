import os
from flask import Flask, request, redirect, render_template
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
import re

app = Flask(__name__)

# Função para extrair informações da página do PDF
def extract_process_and_name(pdf_path, page_number):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        text = page.extract_text()

        if text is None:
            return None, None, None

        lines = text.split('\n')
        process_number = None
        parte_name = None
        identificador_number = None

        for line in lines:
            match_process = re.search(r"Processo:\s*([\d\.\-\/]+)", line)
            match_parte = re.search(r"Parte:\s*([\w\s]+)", line)
            match_identificador = re.search(r"Identificador:\s*(\d{4})", line)

            if match_process:
                process_number = match_process.group(1).replace("-", ".")
            if match_parte:
                parte_name = match_parte.group(1).split()[0].capitalize()
            if match_identificador:
                identificador_number = match_identificador.group(1)

            if process_number and parte_name and identificador_number:
                break

        return process_number, parte_name, identificador_number

# Função para dividir e renomear o PDF
def split_and_rename_pdf(pdf_path):
    pdf_reader = PdfReader(pdf_path)
    num_pages = len(pdf_reader.pages)
    output_folder = os.path.dirname(pdf_path)  # Usar a mesma pasta do arquivo PDF

    for i in range(num_pages):
        process_number, parte_name, identificador_number = extract_process_and_name(pdf_path, i)

        # Substitui informações ausentes
        if process_number is None:
            process_number = "PROCESSO_NAO_ENCONTRADO"
        if parte_name is None:
            parte_name = "NOME_NAO_ENCONTRADO"
        if identificador_number is None:
            identificador_number = "IDENTIFICADOR_NAO_ENCONTRADO"

        # Cria o nome do arquivo
        new_filename = f"Certidao..{parte_name}..{process_number}..{identificador_number}.pdf"
        new_filename = new_filename.replace(" ", "..").replace("/", "-")
        output_path = os.path.join(output_folder, new_filename)

        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[i])

        with open(output_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)

    return f"Páginas separadas e renomeadas com sucesso! Confira os arquivos na pasta {output_folder}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect('/')
    
    file = request.files['file']

    if file.filename == '':
        return redirect('/')

    if file and file.filename.endswith('.pdf'):
        # Salvar o arquivo PDF no servidor
        pdf_path = os.path.join("/tmp", file.filename)
        file.save(pdf_path)

        # Chamar a função para separar e renomear o PDF
        result_message = split_and_rename_pdf(pdf_path)

        return result_message

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
