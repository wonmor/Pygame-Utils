from abc import abstractmethod
from typing import Any, Callable

import gc
import sys

import pygame
from pygame.math import Vector2


class Color:
    BLACK = pygame.color.Color(0, 0, 0)
    CLEAR = pygame.color.Color(0, 0, 0, 0)
    WHITE = pygame.color.Color(255, 255, 255)
    GREY = pygame.color.Color(128, 128, 128)
    GRAY = GREY

    GREEN = pygame.color.Color(0, 255, 0)
    BLUE = pygame.color.Color(0, 0, 255)
    CYAN = pygame.color.Color(0, 255, 255)
    RED = pygame.color.Color(255, 0, 0)
    PINK = pygame.color.Color(255, 102, 178)
    YELLOW = pygame.color.Color(255, 255, 0)
    ORANGE = pygame.color.Color(255, 128, 0)
    MAGENTA = pygame.color.Color(255, 0, 255)


class Alignment:
    TOP_LEFT = "topleft"
    BOTTOM_LEFT = "bottomleft"
    TOP_RIGHT = "topright"
    BOTTOM_RIGHT = "bottomright"
    MID_TOP = "midtop"
    MID_LEFT = "midleft"
    MID_BOTTOM = "midbottom"
    MID_RIGHT = "midright"
    CENTER = "center"


class Graphic_Event:
    def __init__(self) -> None:
        EventManager.add_managed_object(self)

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        ...


class EventManager:
    on_quit = None
    funcs = []
    graphic_events = []

    @classmethod
    def update_managed_objects(cls, graphic_events: list[Graphic_Event]):
        cls.graphic_events = graphic_events

    @classmethod
    def add_managed_object(cls, graphic_event: Graphic_Event):
        cls.graphic_events.append(graphic_event)

    @classmethod
    def set_events(cls, call_backs: Callable | list[Callable]=None, on_quit: Callable=None) -> None:
        if call_backs:
            if type(call_backs) == list:
                cls.funcs = call_backs
            else:
                cls.funcs = [call_backs]

        cls.on_quit = on_quit

    @classmethod
    def add_event(cls, call_back: Callable | list[Callable]):
        cls.funcs.append(call_back)

    @classmethod
    def handle_events(cls) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if cls.on_quit:
                    cls.on_quit()
                pygame.quit()
                sys.exit()
            for func in cls.funcs:
                func(event)
            if not cls.graphic_events:
                continue
            for ge in cls.graphic_events:
                ge.handle_event(event)


class Graphic:
    def __init__(self) -> None:
        self._visible = True
        Canvas.add_managed_object(self)

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        ...


class Canvas:
    main_surface = None
    graphic_elements = []

    @classmethod
    def find_managed_objects(cls):
        """
        Deprecated
        """
        cls.graphic_elements = [obj for obj in gc.get_objects() if isinstance(obj, Graphic)]
        print("This method is deprecated. You do not need to manually get managed objects!")

    @classmethod
    def update_managed_objects(cls, graphic_elements: list[Graphic]):
        cls.graphic_elements = graphic_elements

    @classmethod
    def add_managed_object(cls, graphic: Graphic):
        cls.graphic_elements.append(graphic)

    @classmethod
    def draw(cls) -> None:
        if not cls.graphic_elements:
            return
        if not cls.main_surface:
            cls.main_surface = pygame.display.get_surface()
        for graphic in cls.graphic_elements:
            if graphic.visible:
                graphic.draw(cls.main_surface)


class UiImage(Graphic):
    def __init__(self, image_surface: pygame.surface=None, file_name: str=None, position: Vector2=Vector2(0, 0), size: Vector2=None,
    color_tint: pygame.Color | tuple[int, int, int, int]=(255, 255, 255, 255), blend_mode: int=pygame.BLEND_RGBA_MULT) -> None:
        """
        Specify either the image surface or the image path, not both.
        """
        super().__init__()
        self.position = position
        self.size = size
        self.color_tint = color_tint

        self.image_surface = None
        self.set_image(image_surface, file_name)
        self.tint_image(color_tint, blend_mode)

    def get_image(self) -> pygame.Surface:
        return self.image_surface

    def set_image(self, image_surface: pygame.surface=None, file_name: str=None) -> pygame.Surface:
        if image_surface:
            self.image_surface = image_surface
        else:
            if file_name:
                self.image_surface = pygame.image.load(file_name).convert_alpha()
        self.scale_image()
        self.og_image_surface = self.image_surface.copy()

    def scale_image(self):
        if self.size:
            self.image_surface = pygame.transform.scale(self.image_surface, self.size)
            self.og_image_surface = self.image_surface.copy()

    def tint_image(self, color: pygame.Color | tuple[int, int, int, int], blend_mode: int=pygame.BLEND_RGBA_MULT):
        self.image_surface = self.og_image_surface.copy()
        self.image_surface.fill(color, special_flags=blend_mode)

    def draw(self, surface: pygame.Surface):
        if self.image_surface:
            surface.blit(self.image_surface, self.position)


class Panel(Graphic):
    def __init__(self, position: Vector2=Vector2(0, 0), size: Vector2=None,
    color: pygame.Color | tuple[int, int, int, int]=(80, 80, 80, 100)) -> None:
        super().__init__()
        self.position = position
        self.size = size
        self.color = color
        self.panel_surface = None

    def _render(self, surface: pygame.Surface):
        # If size is set to none, it defaults to the screen/surface size
        if not self.size:
            self.size = surface.get_size()
        self.panel_surface = pygame.Surface(self.size, pygame.SRCALPHA)
        self.panel_surface.fill(self.color)

    def draw(self, surface: pygame.Surface):
        if not self.panel_surface:
            self._render(surface)
        surface.blit(self.panel_surface, self.position)


class Label(Graphic):
    def __init__(self, text: str | Any="", color: pygame.Color | tuple[int, int, int]=(255, 255, 255),
    font_name: str=None, font_size: int=28, position: Vector2=Vector2(0, 0), anchor: Alignment | str="midleft") -> None:
        super().__init__()
        self.font = pygame.font.Font(font_name, font_size)
        self.text = str(text)
        self.color = color
        self.anchor = anchor
        self.position = position
        self._render()

    def _render(self):
        self.image = self.font.render(self.text, True, self.color)
        self.text_rect = self.image.get_rect(**{self.anchor: self.position})

    def clip(self, rect: pygame.Rect):
        self.image = self.image.subsurface(rect)
        self.text_rect = self.image.get_rect(**{self.anchor: self.position})

    def draw(self, surface: pygame.Surface):
        surface.blit(self.image, self.text_rect)

    def set_text(self, text: str):
        self.text = str(text)
        self._render()

    def set_font(self, font_name: str, font_size: int):
        self.font = pygame.font.Font(font_name, font_size)
        self._render()

    def set_color(self, color: tuple[int, int, int]):
        self.color = color
        self._render()

    def set_position(self, position: tuple[int, int], anchor: Alignment | str=None):
        """
        Anchor can be:
        topleft, bottomleft, topright, bottomright
        midtop, midleft, midbottom, midright
        center
        """
        self.position = position
        if anchor:
            self.anchor = anchor

        self.text_rect = self.image.get_rect(**{self.anchor: self.position})


class Button(Graphic, Graphic_Event):
    def __init__(self, image: UiImage=None, on_click: Callable=None,
    position: Vector2=Vector2(0, 0), size: Vector2=Vector2(150, 75),
    color: pygame.Color | tuple[int, int, int]=(255, 255, 255), hover_color: pygame.Color | tuple[int, int, int]=(220, 220, 220),
    pressed_color: pygame.Color | tuple[int, int, int]=(185, 185, 185), disabled_color: pygame.Color | tuple[int, int, int]=(165, 165, 165),
    border_radius: int=0, disabled: bool=False, label: Label=None, label_alignment: Alignment | str="center") -> None:
        Graphic.__init__(self)
        Graphic_Event.__init__(self)
        self.button_image = image
        if self.button_image:
            self.button_image.position = position
            self.button_image.size = size
            self.button_image.scale_image()
            self.rect = image.get_image().get_rect(topleft=position)
        else:
            self.rect = pygame.Rect(position, size)
        self.func = on_click
        self.position = position
        self.size = size
        self.set_color(color)
        self.color = color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.disabled_color = disabled_color
        self.border_radius = border_radius
        self.pressed = False
        self.set_disabled(disabled)
        self.label = label
        self.label_alignment = label_alignment
        if self.label:
            self.label._render()
        self.set_label_pos()

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        if self.button_image:
            self.button_image.visible = value
        if self.label:
            self.label.visible = value
        self._visible = value

    def set_color(self, color: pygame.Color | tuple[int, int, int]):
        self.current_color = color
        if self.button_image:
            self.button_image.tint_image(self.current_color)

    def set_disabled(self, disabled: bool=True):
        self.disabled = disabled
        self.set_color(self.disabled_color)

    def set_label_pos(self):
        """
        Anchor can be:
        topleft, bottomleft, topright, bottomright
        midtop, midleft, midbottom, midright
        center
        """
        if not self.label:
            return

        if self.label_alignment == "center":
            label_offset = (self.size.x/2, self.size.y/2)
        elif self.label_alignment == "midtop":
            label_offset = (self.size.x/2, 0)
        elif self.label_alignment == "midbottom":
            label_offset = (self.size.x/2, self.size.y)
        elif self.label_alignment == "midleft":
            label_offset = (0, self.size.y/2)
        elif self.label_alignment == "bottomleft":
            label_offset = (0, self.size.y)
        elif self.label_alignment == "topright":
            label_offset = (self.size.x, 0)
        elif self.label_alignment == "midright":
            label_offset = (self.size.x, self.size.y/2)
        elif self.label_alignment == "bottomright":
            label_offset = (self.size.x, self.size.y)
        else:
            label_offset = (0, 0)
        label_pos = (self.position.x + self.label.position[0] + label_offset[0], self.position.y + self.label.position[1] + label_offset[1])
        self.label.set_position(label_pos, anchor=self.label_alignment)

    def set_text(self, text: str | Any):
        if self.label:
            self.label.set_text(text)

    def draw(self, surface: pygame.Surface):
        self.mouseover()
        if self.button_image:
            self.button_image.draw(surface)
        else:
            pygame.draw.rect(surface, self.current_color, self.rect, border_radius=self.border_radius)

        if self.label:
            self.label.draw(surface)

    def mouseover(self):
        if self.disabled or self.pressed:
            return
        self.set_color(self.color)
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            self.set_color(self.hover_color)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.disabled or not self.visible:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1:
                return
            pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(pos):
                self.button_press()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button != 1:
                return
            self.button_release()
            pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(pos):
                self.call_back()

    def button_press(self):
        self.pressed = True
        self.set_color(self.pressed_color)

    def button_release(self):
        self.pressed = False

    def call_back(self, *args):
        if self.func:
            return self.func(*args)


class CheckBox(Button):
    def __init__(self, on_value_change: Callable=None,
    position: Vector2=Vector2(0, 0), size: Vector2=Vector2(50, 50),
    color: pygame.Color | tuple[int, int, int]=(255, 255, 255), hover_color: pygame.Color | tuple[int, int, int]=(220, 220, 220),
    pressed_color: pygame.Color | tuple[int, int, int]=(185, 185, 185), disabled_color: pygame.Color | tuple[int, int, int]=(165, 165, 165),
    tick_color: pygame.Color | tuple[int, int, int]=(55, 55, 55), is_on: bool=False,
    border_radius: int=0, disabled: bool=False, label_alignment: Alignment | str="midleft") -> None:
        super().__init__(None, on_value_change, position, size, color, hover_color, pressed_color, disabled_color,
        border_radius, disabled, None, label_alignment)
        self.tick_color = tick_color
        self.is_on = is_on
        self.tick_rect = pygame.Rect(Vector2(position.x + size.x/4, position.y + size.y/4), Vector2(size.x / 2, size.y / 2))

    def draw(self, surface: pygame.Surface):
        super().draw(surface)
        if self.is_on:
            pygame.draw.rect(surface=surface, color=self.tick_color, rect=self.tick_rect)

    def call_back(self):
        self.is_on = not self.is_on
        super().call_back(self.is_on)


class InputBox(Label, Graphic_Event):
    def __init__(self, on_value_change: Callable=None, on_delete: Callable=None,
    on_submit: Callable=None, on_select: Callable=None, submit_on_return: bool=True,
    position: Vector2=Vector2(0, 0), size: Vector2=Vector2(150, 35),
    box_color: pygame.Color | tuple[int, int, int]=(255, 255, 255), border_thickness: int=2,
    border_color_active: pygame.Color | tuple[int, int, int]=(20, 20, 20),
    border_color_inactive: pygame.Color | tuple[int, int, int]=(100, 100, 100),
    text_color: pygame.Color | tuple[int, int, int]=(20, 20, 20), text: str | Any="", font_name: str=None, font_size: int=28):
        super().__init__(text, text_color, font_name, font_size, position)
        Graphic_Event.__init__(self)
        self.rect = pygame.Rect(position, size)
        self.position = position
        self.size = size
        self.box_color = box_color
        self.border_thickness = border_thickness
        self.border_color = border_color_inactive
        self.border_color_active = border_color_active
        self.border_color_inactive = border_color_inactive
        self.active = False
        self.on_value_change = on_value_change
        self.on_delete = on_delete
        self.on_submit = on_submit
        self.on_select = on_select
        self.submit_on_return = submit_on_return

    def draw(self, surface: pygame.Surface):
        # Overflow
        self.rect.w = max(self.size.x, self.image.get_width()+10)
        # Draw text and rect
        surface.blit(self.image, (self.rect.x+5, self.rect.y + self.rect.height/4))
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_thickness)

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.visible:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect
            if self.rect.collidepoint(event.pos):
                self.call_back(self.on_select)
                # Toggle the active variable
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box
            self.set_border_state()
        if event.type == pygame.KEYDOWN:
            if not self.active:
                return
            if event.key == pygame.K_RETURN:
                if self.submit_on_return:
                    self.submit()
            elif event.key == pygame.K_BACKSPACE:
                self.call_back(self.on_delete)
                self.text = self.text[:-1]
            else:
                self.call_back(self.on_value_change)
                self.text += event.unicode
            # Re-render the text
            self._render()

    def submit(self):
        self.call_back(self.on_submit)
        self.text = ""
        self.active = False
        self.set_border_state()

    def set_border_state(self):
        self.border_color = self.border_color_active if self.active else self.border_color_inactive

    def call_back(self, func, *args):
        if func:
            return func(self.text, *args)


class Shape(object):
    def __init__(self, position: Vector2=Vector2(0, 0), color: pygame.Color | tuple[int, int, int]=(0, 0, 0)) -> None:
        self.position = position
        self.color = color

    @abstractmethod
    def move(self, x: int=None, y: int=None):
        ...

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        ...


class Square(Shape):
    def __init__(self, position: Vector2=Vector2(0, 0), size: Vector2=Vector2(100, 100),
    color: pygame.Color | tuple[int, int, int]=(0, 0, 0)) -> None:
        super().__init__(position, color)
        self.size = size
        self.rect = pygame.Rect(position, size)

    def move(self, x: int=None, y: int=None):
        if x and y:
            self.position = pygame.Rect(self.position, Vector2(x, y))
        elif x:
            self.position = pygame.Rect(self.position, Vector2(x, self.position.y))
        else:
            self.position = pygame.Rect(self.position, Vector2(self.position.x, y))

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface=surface, color=self.color, rect=self.rect)


class Circle(Shape):
    def __init__(self, position: Vector2=Vector2(0, 0), radius: int=10, color: pygame.Color | tuple[int, int, int]=(0, 0, 0)) -> None:
        super().__init__(position, color)
        self.radius = radius

    def move(self, x: int=None, y: int=None):
        if x and y:
            self.position = Vector2(x, y)
        elif x:
            self.position = Vector2(x, self.position.y)
        else:
            self.position = Vector2(self.position.x, y)

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface=surface, color=self.color, center=self.position, radius=self.radius)
