from dataclasses import dataclass, field
import textwrap
from typing import Iterable, List, Optional, Union


INDENT_SIZE = 2


class Statement:
    pass


class StatementsList(list[Statement]):
    def __init__(self, iterable: Iterable[Statement] = []):
        super().__init__(iterable)

    def __str__(self):
        result = ""
        for idx, child in enumerate(self):
            result += str(child) + "\n"
            if (
                isinstance(child, Assignment)
                and child.element.children is not None
                and idx != len(self) - 1
            ):
                result += "\n"
        return result.strip()

    def __add__(self, x: Union[Statement, List[Statement]]):
        if isinstance(x, Statement):
            return StatementsList(super().__add__([x]))
        else:
            return StatementsList(super().__add__(x))


class Properties(list[str]):
    def __init__(self, iterable: Iterable[str] = []):
        super().__init__(iterable)

    def __str__(self):
        result: str = ""
        not_empty_props_count = len(self)
        for prop in self[::-1]:
            if prop:
                break
            not_empty_props_count -= 1
        for prop in self[:not_empty_props_count]:
            result += ' "' + prop.replace("\n", "\\n").replace('"', '\\"') + '"'
        return result.strip()


@dataclass
class Element(Statement):
    keyword: str
    properties: Properties = field(default_factory=Properties)
    children: Optional[StatementsList] = None

    def __str__(self):
        result = self.keyword
        if self.properties:
            result += f" {self.properties}"
        if self.children is not None:
            result += " {"
            if self.children:
                result += (
                    "\n" + textwrap.indent(str(self.children), " " * INDENT_SIZE) + "\n"
                )
            result += "}"
        return result


@dataclass
class Assignment(Statement):
    identifier: str
    element: Element

    def __str__(self):
        return f"{self.identifier} = {self.element}"


@dataclass
class Relationship(Statement):
    source: str
    target: str
    properties: Properties = field(default_factory=Properties)

    def __str__(self):
        result = f"{self.source} -> {self.target}"
        if self.properties:
            result += f' {self.properties}'
        return result
