#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validation of required tags by Facebook in XML Merchants v2 feed.
"""

import argparse
import logging
import requests
from os import listdir
from os.path import isfile, join
from lxml import etree


def setup_logger(name, level=logging.DEBUG):
    logging.basicConfig(level=level, format="[%(levelname)s] %(asctime)s: %(message)s")
    for handler in logging.root.handlers:
        handler.addFilter(logging.Filter(name))
    return logging.getLogger(name)


class Parser(object):

    def __init__(self, logger, file_path, item_tag='item', no_check_link=False, no_check_img=False, **kwargs):
        self.file_path = file_path
        self.no_check_link = no_check_link
        self.no_check_img = no_check_img
        self.logger = logger

        self._ITEM_TAG = item_tag
        self.g = '{http://base.google.com/ns/1.0}'
        self.element = None

        self.count = 0
        self.count_img = 0
        self.count_products = 0

        self.REQUIRED_TAGS = {
            'id',
            'title',
            'description',
            'google_product_category',
            'price',
            'brand',
            'link',
            'image_link',
            }

    def fast_iter(self):
        """
        Incrementally iterate over products in locally stored feed.
        Parse current product and store data in database, then move on next.
        """
        try:
            context = etree.iterparse(self.file_path, events=('end', ), tag=self._ITEM_TAG)
            for event, self.element in context:
                try:
                    self.parse()
                    self.count_products += 1

                except ValueError as e:
                    print(e.args)    # convert price text to float

                self.element.clear()
                while self.element.getprevious() is not None:
                    del self.element.getparent()[0]
            del context
        except etree.XMLSyntaxError as e:
            self.logger.critical(e)

    def check_link(self, link):
        try:
            r = requests.head(link)
        except Exception as e:
            self.logger.exception(e)
            return False

        if r.status_code == 200:
            return True

        self.logger.critical("Bad link [%s]: %s", r.status_code, link)
        return False

    def parse(self):
        ok_elements = set()
        _id = -1

        for element in self.element.iterchildren('*'):
            elem_text = element.text.strip() if element.text else ''

            if element.tag == self.g + 'id' and len(elem_text) > 0:
                ok_elements.add('id')
                _id = elem_text
                self.count += 1

            elif element.tag == self.g + 'title' and len(elem_text) > 0:
                ok_elements.add('title')
                if elem_text.isupper():
                    self.logger.warning('Title is upper cased (item id=%s)', _id)

            elif element.tag == self.g + 'description' and len(elem_text) > 0:
                ok_elements.add('description')

            elif element.tag == self.g + 'google_product_category' and len(elem_text) > 0:
                ok_elements.add('google_product_category')

            elif element.tag == self.g + 'price' and len(elem_text) > 0:
                ok_elements.add('price')

            elif element.tag == self.g + 'brand' and len(elem_text) > 0:
                ok_elements.add('brand')

            elif element.tag == self.g + 'link' and len(elem_text) > 0:
                if self.no_check_link:
                    ok_elements.add('link')
                elif self.check_link(elem_text):
                    ok_elements.add('link')

            if element.tag == self.g + 'image_link' and len(elem_text) > 0:
                if self.no_check_img:
                    ok_elements.add('image_link')
                    self.count_img += 1
                elif self.check_link(elem_text):
                    ok_elements.add('image_link')
                    self.count_img += 1

        if not ok_elements.issuperset(self.REQUIRED_TAGS):
            self.logger.warning('Missing %s in element (id=%s)', self.REQUIRED_TAGS - ok_elements, _id)


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('path', help='Process all files in specified folder.')
    arg_parser.add_argument('--no-check-link', action='store_true', default=False, help='Do not check product links')
    arg_parser.add_argument('--no-check-img', action='store_true', default=False, help='Do not check image links')
    arg_parser.add_argument('--filter', action='store', help='Filter file names by string.')
    arg_parser.add_argument('--no-process', action='store_true', default=False, help='Print files to parse.')
    arg_parser.add_argument('--log-level', action='store', choices=["info", "warning", "error", "critical"], default="info")

    args = arg_parser.parse_args()
    logger = setup_logger(__name__)
    result = {}

    for file in sorted([f for f in listdir(args.path) if isfile(join(args.path, f))]):

        # skip hidden
        if file[0] == '.':
            continue

        # skip files not matched by filter
        if args.filter and args.filter not in file:
            continue

        full_path = join(args.path, file)

        logger.info("File " + full_path)

        if not args.no_process:
            logger.setLevel(args.log_level.upper())
            p = Parser(logger, full_path, no_check_link=args.no_check_link, no_check_img=args.no_check_img)
            try:
                p.fast_iter()
            except Exception as e:
                logger.exception(e)

            logger.setLevel(logging.INFO)
            logger.info("File %s -- products: %s ids:%s images:%s", full_path, p.count_products, p.count, p.count_img)
            result[full_path] = (p.count, p.count_img)

    logger.info("FINISHED")
    for key, value in result.items():
        logger.info("File %s -- ids:%s images:%s", key, value[0], value[1])
