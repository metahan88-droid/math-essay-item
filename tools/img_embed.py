#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HWPX에 PNG 도해를 삽입하는 헬퍼.

원본 템플릿의 hp:pic을 역산한 규격:
· BinData/imageN.png 로 zip에 넣고 content.hpf에 opf:item 등록
· 본문에는 hp:pic 요소를 treatAsChar="1"로 넣어 문단 안 글자처럼 배치
· orgSz/imgRect/imgClip/imgDim = 원본 픽셀 크기를 HWPUNIT(px * 75/2 가 아니라
  임의 지정 가능 — 여기서는 1px = 30 HWPUNIT로 고정해 orgSz를 만들고
  curSz/sz 로 실제 표시 크기를 지정)
· lineseg 의 vertsize = 표시 높이. treatAsChar 이므로 셀 높이 계산에 그대로 들어간다.
"""
import os, re, struct

_pic_id = [90000]


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(26)
    assert head[1:4] == b'PNG', path
    w, h = struct.unpack('>II', head[16:24])
    return w, h


def pic_xml(bin_id, disp_w, px_w, px_h):
    """표시 폭 disp_w(HWPUNIT)로 비율 유지 hp:pic 생성. -> (xml, disp_h)"""
    _pic_id[0] += 1
    org_w, org_h = px_w * 30, px_h * 30          # 명목 원본 크기
    disp_h = int(round(disp_w * px_h / px_w))
    sca = disp_w / org_w
    return (
        f'<hp:pic id="{_pic_id[0]}" zOrder="{_pic_id[0]-89950}" numberingType="PICTURE" '
        f'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" '
        f'href="" groupLevel="0" instid="{_pic_id[0]+7000000}" reverse="0">'
        f'<hp:offset x="0" y="0"/><hp:orgSz width="{org_w}" height="{org_h}"/>'
        f'<hp:curSz width="{disp_w}" height="{disp_h}"/><hp:flip horizontal="0" vertical="0"/>'
        f'<hp:rotationInfo angle="0" centerX="{disp_w//2}" centerY="{disp_h//2}" rotateimage="1"/>'
        f'<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
        f'<hc:scaMatrix e1="{sca:.6f}" e2="0" e3="0" e4="0" e5="{sca:.6f}" e6="0"/>'
        f'<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
        f'<hc:img binaryItemIDRef="{bin_id}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
        f'<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{org_w}" y="0"/>'
        f'<hc:pt2 x="{org_w}" y="{org_h}"/><hc:pt3 x="0" y="{org_h}"/></hp:imgRect>'
        f'<hp:imgClip left="0" right="{org_w}" top="0" bottom="{org_h}"/>'
        f'<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:imgDim dimwidth="{org_w}" dimheight="{org_h}"/><hp:effects/>'
        f'<hp:sz width="{disp_w}" widthRelTo="ABSOLUTE" height="{disp_h}" heightRelTo="ABSOLUTE" protect="0"/>'
        f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" '
        f'holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" '
        f'horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
        f'<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
        f'<hp:shapeComment>그림</hp:shapeComment></hp:pic>', disp_h)


def pic_paragraph(bin_id, disp_w, px_w, px_h, pid, horzsize, cursor):
    """도해 한 장을 담은 가운데정렬 문단 XML. -> (xml, 차지 높이)"""
    pic, disp_h = pic_xml(bin_id, disp_w, px_w, px_h)
    _pic_id[0] += 1
    seg = (f'<hp:lineseg textpos="0" vertpos="{cursor}" vertsize="{disp_h}" '
           f'textheight="{disp_h}" baseline="{int(disp_h*0.85)}" spacing="0" '
           f'horzpos="0" horzsize="{horzsize}" flags="393216"/>')
    xml = (f'<hp:p id="{_pic_id[0]}" paraPrIDRef="{pid}" styleIDRef="0" '
           f'pageBreak="0" columnBreak="0" merged="0">'
           f'<hp:run charPrIDRef="1">{pic}<hp:t/></hp:run>'
           f'<hp:linesegarray>{seg}</hp:linesegarray></hp:p>')
    return xml, disp_h


def register_images(out_dir, images):
    """images: {bin_id: png_path}. BinData 복사 + content.hpf 등록."""
    os.makedirs(os.path.join(out_dir, 'BinData'), exist_ok=True)
    hpf_path = os.path.join(out_dir, 'Contents', 'content.hpf')
    hpf = open(hpf_path, encoding='utf-8').read()
    for bid, path in images.items():
        dst = os.path.join(out_dir, 'BinData', f'{bid}.png')
        open(dst, 'wb').write(open(path, 'rb').read())
        if f'id="{bid}"' not in hpf:
            item = (f'<opf:item id="{bid}" href="BinData/{bid}.png" '
                    f'media-type="image/png" isEmbeded="1"/>')
            hpf = hpf.replace('<opf:item id="section0"', item + '<opf:item id="section0"')
    open(hpf_path, 'w', encoding='utf-8').write(hpf)
