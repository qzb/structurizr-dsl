from dataclasses import dataclass, field
import textwrap
import dsl
from typing import Any, Dict, Generic, List, TypeVar
from slugify import slugify

T = TypeVar("T")

INDENT_SIZE = 2
COMPONENT_PROP_NAME = "structurizr_component"


__all__ = ["included_in", "relates_to", "ComponentsGroup"]


def docstring_to_description(obj: Any) -> str:
    ret = getattr(obj, "__doc__", "")
    ret = textwrap.dedent(ret)
    ret, *_ = ret.strip().split("\n\n", maxsplit=1)
    return ret


class Element:
    name: str

    def id(self, prefix: str = ""):
        return slugify(f"{prefix} {self.name}", separator="_")

    def dsl(self, id_prefix: str = "") -> dsl.StatementsList:
        return dsl.StatementsList()


@dataclass
class Relation:
    source: Element
    target: Element
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def dsl(self, id_prefix: str = "") -> dsl.StatementsList:
        return dsl.StatementsList(
            [
                dsl.Relationship(
                    self.source.id(id_prefix),
                    self.target.id(id_prefix),
                    dsl.Properties([self.description, ", ".join(self.tags)]),
                )
            ]
        )


@dataclass(frozen=True)
class Component(Element):
    name: str
    description: str = ""
    technology: str = ""
    url: str = ""
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    perspectives: Dict[str, str] = field(default_factory=dict)
    relations: List[Relation] = field(default_factory=list, init=False)

    def add_relation(self, relation: Relation):
        self.relations.append(relation)

    def dsl(self, id_prefix: str = "") -> dsl.StatementsList:
        children = [
            dsl.Element("description", dsl.Properties([self.description])),
            dsl.Element("technology", dsl.Properties([self.technology])),
            dsl.Element("url", dsl.Properties([self.url])),
            dsl.Element("tags", dsl.Properties(self.tags)),
            dsl.Element(
                "properties",
                children=dsl.StatementsList(
                    dsl.Element(keyword=k, properties=dsl.Properties([v]))
                    for k, v in self.properties
                ),
            ),
            dsl.Element(
                "perspectives",
                children=dsl.StatementsList(
                    dsl.Element(keyword=k, properties=dsl.Properties([v]))
                    for k, v in self.perspectives
                ),
            ),
        ]
        relations = sum(
            [r.dsl(id_prefix=id_prefix) for r in self.relations], dsl.StatementsList()
        )
        element = dsl.Assignment(
            self.id(id_prefix),
            dsl.Element(
                "component",
                dsl.Properties([self.name]),
                dsl.StatementsList(
                    c for c in children if any(c.properties) or c.children
                ),
            ),
        )
        return dsl.StatementsList([element]) + relations


E = TypeVar("E", bound=Element)


@dataclass
class GenericGroup(Element, Generic[E]):
    name: str
    __children: List[E] = field(default_factory=lambda: [])

    def add_element(self, elem: E):
        self.__children.append(elem)

    def dsl(self, id_prefix: str = "") -> dsl.StatementsList:
        identifier = self.id(id_prefix)
        children = dsl.StatementsList()
        relations = dsl.StatementsList()
        for component in self.__children:
            stmts = component.dsl(id_prefix=identifier)
            children.extend(s for s in stmts if not isinstance(s, dsl.Relationship))
            relations.extend(s for s in stmts if isinstance(s, dsl.Relationship))
        element = dsl.Element(
            "group",
            dsl.Properties([self.name]),
            children,
        )
        return dsl.StatementsList() + dsl.Assignment(identifier, element) + relations


class ComponentsGroup(GenericGroup[Component]):
    pass


def get_component_for_object(obj: Any) -> Component:
    if not hasattr(obj, COMPONENT_PROP_NAME):
        component = Component(
            name=getattr(obj, "__name__", ""),
            description=docstring_to_description(obj),
        )
        setattr(obj, COMPONENT_PROP_NAME, component)
    return getattr(obj, COMPONENT_PROP_NAME)


def relates_to(target: Any, description: str = ""):
    def decorator(obj: T) -> T:
        if isinstance(target, str):
            target_component = Component(name=target)
        elif not isinstance(target, Element):
            target_component = get_component_for_object(target)
        else:
            target_component = target
        component = get_component_for_object(obj)
        component.add_relation(Relation(component, target_component, description))
        return obj

    return decorator


def included_in(parent: GenericGroup[Component]):
    def decorator(obj: T) -> T:
        component = get_component_for_object(obj)
        parent.add_element(component)
        return obj

    return decorator


g = ComponentsGroup(name="test")


@included_in(g)
@relates_to("tasks_abc", "uses")
def foo():
    """
    first line
    second line

    second paragraph
    """


@included_in(g)
@relates_to(foo, "uses")
def abc():
    """
    first line
    second line

    second paragraph
    """


print(g.dsl())
