import os
import re

import argparse
import glob
import shutil
import zipfile
from pyrsistent import optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from tqdm import tqdm


MOX2PDF_TEMP_DIR = '.mox2pdf'


def extract_epub(epub_path):
    with zipfile.ZipFile(epub_path, 'r') as archive:
        archive.extractall(path=os.path.join(os.getcwd(), MOX2PDF_TEMP_DIR))


def get_image_path(html_path):
    with open(html_path, 'rb') as html:
        content = html.read().decode('utf-8')
        image_path = re.search(r'vol-[0-9]{6}\.(jpg|png)', content, re.MULTILINE)
        if image_path is None:
            raise Exception("Cannot get image path from: {}".format(html_path))
        return image_path.group()


def get_image_paths():
    temp_dir = os.path.join(os.getcwd(), MOX2PDF_TEMP_DIR)
    html_dir = os.path.join(temp_dir, 'html')
    image_dir = os.path.join(temp_dir, 'image')
    image_paths = []

    if os.path.exists(os.path.join(image_dir, 'cover.jpg')):
        image_paths.append(os.path.join(image_dir, 'cover.jpg'))
    elif os.path.exists(os.path.join(image_dir, 'cover.png')):
        image_paths.append(os.path.join(image_dir, 'cover.png'))
    else:
        print('No cover image detected.')

    image_dict = {}
    glob_pattern = ''
    if os.path.exists(os.path.join(html_dir, '1.html')):
        glob_pattern = '[0-9]*.html'
    elif os.path.exists(os.path.join(html_dir, '1.xhtml')):
        glob_pattern = '[0-9]*.xhtml'
    else:
        raise Exception('Cannot find first HTML file for indexing images: {}'.format(os.path.join(html_dir, '1.html')))

    for html_path in glob.glob(os.path.join(html_dir, glob_pattern)):
        image_path = get_image_path(html_path)
        html_file = os.path.split(html_path)[-1]
        image_dict[int(html_file[:-5])] = image_path

    for index in sorted(image_dict):
        image_paths.append(os.path.join(image_dir, image_dict[index]))
    
    if os.path.exists(os.path.join(image_dir, 'createby.jpg')):
        image_paths.append(os.path.join(image_dir, 'createby.jpg'))
    elif os.path.exists(os.path.join(image_dir, 'createby.png')):
        image_paths.append(os.path.join(image_dir, 'createby.png'))
    else:
        print('No createby image detected.')

    return image_paths


def generate_pdf(pdf_path, image_paths):
    test_pdf = canvas.Canvas('temp.pdf')
    pdf = canvas.Canvas(pdf_path)
    a4_ratio = A4[0] / A4[1]
    count = 0
    for image_path in tqdm(image_paths):
        width, height = test_pdf.drawImage(image_path, 0, 0)
        ratio = width / height
        if ratio > a4_ratio:
            pdf.drawImage(image_path, 0, 0, width=A4[0], anchor='sw', preserveAspectRatio=True)
        else:
            pdf.drawImage(image_path, 0, 0, height=A4[1], anchor='sw', preserveAspectRatio=True)
        pdf.showPage()
        count += 1
    pdf.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert EPub comics downloaded from mox.moe to PDF A4 format.')
    parser.add_argument('epub_path', type=str, help='Path to the EPub file.')
    parser.add_argument('-p', '--preserve', action='store_true', help='Preserve the {} not to be removed.'.format(MOX2PDF_TEMP_DIR))
    parser.add_argument('-o', '--output', type=str, required=False, help='The output PDF file name.')
    args = parser.parse_args()

    print('Extracting epub file:', args.epub_path)
    extract_epub(args.epub_path)
    print('Indexing images...')
    image_paths = get_image_paths()

    pdf_file_name = args.output if args.output else os.path.split(os.path.splitext(args.epub_path)[0] + '.pdf')[1]
    print('Generating PDF:', pdf_file_name)
    generate_pdf(pdf_file_name, image_paths)
    if not args.preserve:
        print('Cleaning workspace...')
        shutil.rmtree(os.path.join(os.getcwd(), MOX2PDF_TEMP_DIR))
    print('All done.')
