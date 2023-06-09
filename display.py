from paddleocr import PaddleOCR, draw_ocr, PPStructure, draw_structure_result
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import math
import cv2


def create_font(txt, sz, font_path="./doc/fonts/simfang.ttf"):
    font_size = int(sz[1] * 0.99)
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    length = font.getsize(txt)[0]
    if length > sz[0]:
        font_size = int(font_size * sz[0] / length)
        font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    return font


def draw_box_txt_fine(img_size, box, txt, font_path="./doc/fonts/simfang.ttf"):
    box_height = int(
        math.sqrt((box[0][0] - box[3][0])**2 + (box[0][1] - box[3][1])**2))
    box_width = int(
        math.sqrt((box[0][0] - box[1][0])**2 + (box[0][1] - box[1][1])**2))

    if box_height > 2 * box_width and box_height > 30:
        img_text = Image.new('RGB', (box_height, box_width), (255, 255, 255))
        draw_text = ImageDraw.Draw(img_text)
        if txt:
            font = create_font(txt, (box_height, box_width), font_path)
            draw_text.text([0, 0], txt, fill=(0, 0, 0), font=font)
        img_text = img_text.transpose(Image.ROTATE_270)
    else:
        img_text = Image.new('RGB', (box_width, box_height), (255, 255, 255))
        draw_text = ImageDraw.Draw(img_text)
        if txt:
            font = create_font(txt, (box_width, box_height), font_path)
            draw_text.text([0, 0], txt, fill=(0, 0, 0), font=font)

    pts1 = np.float32(
        [[0, 0], [box_width, 0], [box_width, box_height], [0, box_height]])
    pts2 = np.array(box, dtype=np.float32)
    M = cv2.getPerspectiveTransform(pts1, pts2)

    img_text = np.array(img_text, dtype=np.uint8)
    img_right_text = cv2.warpPerspective(
        img_text,
        M,
        img_size,
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255))
    return


def draw_ocr_box_txt(image,
                     boxes,
                     txts=None,
                     scores=None,
                     drop_score=0.5,
                     font_path="./doc/fonts/simfang.ttf"):
    h, w = image.height, image.width
    img_left = image.copy()
    img_right = np.ones((h, w, 3), dtype=np.uint8) * 255
    random.seed(0)

    draw_left = ImageDraw.Draw(img_left)
    if txts is None or len(txts) != len(boxes):
        txts = [None] * len(boxes)
    for idx, (box, txt) in enumerate(zip(boxes, txts)):
        if scores is not None and scores[idx] < drop_score:
            continue
        color = (random.randint(0, 255), random.randint(0, 255),
                 random.randint(0, 255))
        draw_left.polygon(box, fill=color)
        img_right_text = draw_box_txt_fine((w, h), box, txt, font_path)
        pts = np.array(box, np.int32).reshape((-1, 1, 2))
        cv2.polylines(img_right_text, [pts], True, color, 1)
        img_right = cv2.bitwise_and(img_right, img_right_text)
    img_left = Image.blend(image, img_left, 0.5)
    img_show = Image.new('RGB', (w * 2, h), (255, 255, 255))
    img_show.paste(img_left, (0, 0, w, h))
    img_show.paste(Image.fromarray(img_right), (w, 0, w * 2, h))
    return np.array(img_show)


def display():
    global ocr, image, width, height
    img_path = './image10.jpg'
    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    result = ocr.ocr(img_path, cls=True)
    image = Image.open(img_path).convert('RGB')
    boxes = [detection[0] for line in result for detection in line]
    im_show = draw_ocr(image, boxes)
    im_show = Image.fromarray(im_show)
    im_show = np.array(im_show)
    im_show = cv2.cvtColor(im_show, cv2.COLOR_RGB2BGR)
    table_engine = PPStructure(show_log=False, lang="en")
    table_result = table_engine(img_path)
    print("Output of Box, Text, and Score:")
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            print(line)
    im_show_table = draw_structure_result(
        image, table_result, font_path="./simfang.ttf")
    im_show_table = Image.fromarray(im_show_table)
    width, height = im_show_table.size
    cropped_im_show_table = im_show_table.crop((width / 2, 0, width, height))
    cropped_im_show_table = np.array(cropped_im_show_table)
    cropped_im_show_table = cv2.cvtColor(cropped_im_show_table, cv2.COLOR_RGB2BGR)
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    if im_show.shape[0] != cropped_im_show_table.shape[0]:
        if im_show.shape[0] > cropped_im_show_table.shape[0]:
            im_show = cv2.resize(
                im_show,
                (im_show.shape[1] * cropped_im_show_table.shape[0] // im_show.shape[0], cropped_im_show_table.shape[0]))
        else:
            cropped_im_show_table = cv2.resize(cropped_im_show_table, (
                cropped_im_show_table.shape[1] * im_show.shape[0] // cropped_im_show_table.shape[0], im_show.shape[0]))
    im_concat = cv2.hconcat([image, im_show, cropped_im_show_table])
    cv2.imwrite("im_result.jpg", im_concat)


if __name__ == '__main__':
    display()