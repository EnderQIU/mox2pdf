import os
import re

import argparse
import glob
import shutil
import zipfile
from pyrsistent import optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


MOX2PDF_TEMP_DIR = '.mox2pdf'


def extract_epub(epub_path):
    with zipfile.ZipFile(epub_path, 'r') as archive:
        archive.extractall(path=os.path.join(os.getcwd(), MOX2PDF_TEMP_DIR))


def get_image_path(html_path):
    with open(html_path, 'r') as html:
        content = html.read()
        image_path = re.search(r'vol-[0-9]{6}\.jpg', content, re.MULTILINE)
        if image_path is None:
            raise Exception("Cannot get image path from:", html_path)
        return image_path.group()


def get_image_paths():
    temp_dir = os.path.join(os.getcwd(), MOX2PDF_TEMP_DIR)
    html_dir = os.path.join(temp_dir, 'html')
    image_dir = os.path.join(temp_dir, 'image')
    image_paths = [os.path.join(image_dir, 'cover.jpg')]
    image_dict = {}
    for html_path in glob.glob(os.path.join(html_dir, '[0-9]*.html')):
        print('HTML', html_path)
        image_path = get_image_path(html_path)
        print('IMAGE', image_path)
        html_file = os.path.split(html_path)[-1]
        image_dict[int(html_file[:-5])] = image_path

    for index in sorted(image_dict):
        image_paths.append(os.path.join(image_dir, image_dict[index]))
    
    image_paths.append(os.path.join(image_dir, 'createby.png'))
    return image_paths


def generate_pdf(pdf_path, image_paths):
    test_pdf = canvas.Canvas('temp.pdf')
    pdf = canvas.Canvas(pdf_path)
    a4_ratio = A4[0] / A4[1]
    for image_path in image_paths:
        width, height = test_pdf.drawImage(image_path, 0, 0)
        ratio = width / height
        if ratio > a4_ratio:
            pdf.drawImage(image_path, 0, 0, width=A4[0], anchor='sw', preserveAspectRatio=True)
        else:
            pdf.drawImage(image_path, 0, 0, height=A4[1], anchor='sw', preserveAspectRatio=True)
        pdf.showPage()
    pdf.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert EPub comics downloaded from mox.moe to PDF A4 format.')
    parser.add_argument('epub_path', type=str, help='Path to the EPub file.')
    parser.add_argument('-p', '--preserve', action='store_true', help='Preserve the {} not to be removed.'.format(MOX2PDF_TEMP_DIR))
    parser.add_argument('-o', '--output', type=str, required=False, help='The output PDF file name.')
    args = parser.parse_args()

    extract_epub(args.epub_path)
    image_paths = get_image_paths(args.epub_path)

    generate_pdf(args.output if args.output else os.path.split(os.path.splitext(args.epub_path)[0] + '.pdf')[1], image_paths)
    if not args.preserve:
        shutil.rmtree(os.path.join(os.getcwd(), MOX2PDF_TEMP_DIR))
