#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import unicode_literals, division, absolute_import, print_function

from collections import OrderedDict
import regex as re
from sigil_bs4 import BeautifulSoup, Tag

# from bs4 import BeautifulSoup, NavigableString, Tag

DEBUG = None


def attrMatch(attr_str, method, srch_str):
    if method == "normal":
        return attr_str == srch_str
    elif method == "regex":
        if re.match(r"""%s""" % srch_str, attr_str, re.U) is not None:
            return True
        else:
            return False


def attrs_equal(a, b):
    """Compare two attribute dictionaries for exact equality."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if set(a.keys()) != set(b.keys()):
        return False
    return all(a[k] == b[k] for k in a)


class MarkupParser(object):
    """The criteria parameter dictionary specs
    criteria['html']              Param 1 - the contents of the (x)html file: unicode text.
    criteria['action']            Param 2 - action to take: unicode text ('modify' or 'delete')
    criteria['tag']               Param 3 - tag to alter/delete: unicode text
    criteria['attrib']            Param 4 - attribute to use in match: unicode text or None
    criteria['srch_str']          Param 5 - value of the attribute to use in match: unicode text (literal or regexp) or None
    criteria['srch_method']       Param 6 - is the value given literal or a regexp: boolean
    """

    def __init__(self, criteria):
        self.wipml = criteria["html"]
        self.action = criteria["action"]
        self.tag = criteria["tag"]
        self.attrib = criteria["attrib"]
        self.srch_str = criteria["srch_str"]
        self.srch_method = criteria["srch_method"]
        self.occurrences = 0

    def processml(self):
        if self.action == "merge":
            soup = BeautifulSoup(self.wipml, "xml")
            # Perform merging
            newsoup = self.merge_adjacent_tags(soup)
            # print(f'html: {newsoup.serialize_xhtml}\noccurrences: {self.occurrences}')
            return str(newsoup), self.occurrences
        else:
            return None, self.occurrences

    def merge_adjacent_tags(self, soup):
        """Recursively merge adjacent tags with same name and attributes."""
        # Find all elements that can have siblings (avoid text-only roots)
        for parent in soup.find_all():
            children = [
                child for child in list(parent.children) if isinstance(child, Tag)
            ]
            i = 0
            if DEBUG is not None:
                print(f"parent has {len(children)} children")
            while i < len(children) - 1:
                current = children[i]
                next_node = children[i + 1]
                if DEBUG is not None:
                    print(f"i: {i} -- current: {current.name}---------| {str(current)}")
                    print(f"next_node: {next_node.name}---------| {str(next_node)}")

                # Only process tag nodes (skip NavigableString, Comment, etc.)
                if not (hasattr(current, "name") and hasattr(next_node, "name")):
                    i += 1
                    continue

                if (
                    current.name == next_node.name
                    and current.name is not None
                    and (
                        self.attrib is None
                        or (
                            self.attrib in current.attrs.keys()
                            and attrMatch(
                                current.attrs[self.attrib],
                                self.srch_method,
                                self.srch_str,
                            )
                        )
                    )
                    and (self.tag is None or current.name == self.tag)
                    and attrs_equal(current.attrs, next_node.attrs)
                ):
                    # Move all contents of next_node into current
                    if DEBUG is not None:
                        print(
                            f"current_node: {str(current)}\nnext_node: {str(next_node)}"
                        )
                    for child in list(next_node.contents):
                        current.append(child)
                    next_node.decompose()  # Remove the merged node
                    self.occurrences += 1
                    # Rebuild children list after modification
                    children = [
                        child
                        for child in list(parent.children)
                        if isinstance(child, Tag)
                    ]
                else:
                    i += 1
            if DEBUG is not None:
                print("loop next find object")

        # Recursion is implicit via full tree traversal above
        return soup
