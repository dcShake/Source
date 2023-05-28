
from discord import ui, PartialEmoji, Interaction, utils
from Classes.pages.source import FrontPageSource, ListPageSource
from Classes.pages.page import Pages
from typing import Any, TYPE_CHECKING, Optional
from Classes import _
Group = Item = Any

if TYPE_CHECKING:
    from Classes import ShakeContext, ShakeBot, MISSING
    from Classes.pages import CategoricalMenu
else:
    MISSING = None
    CategoricalMenu = Pages
    from discord.ext.commands import Context as ShakeContext, Bot as ShakeBot

class CategoricalSelect(ui.Select):
    view: CategoricalMenu

    def __init__(self, ctx: ShakeContext, source: ListPageSource, describe: Optional[bool] = True):
        super().__init__(placeholder=_("Choose a Category..."), min_values=1, max_values=1, row=0,)
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.find = dict()
        self.source: ListPageSource = source
        self.__categories: Optional[dict[Group, list[Item]]] = None
        self.describe: Optional[bool] = describe
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        self.__fill_options()
        return self

    @property
    def categories(self) -> dict[Group, list[Item]]:
        return self.__categories

    @categories.setter
    def categories(self, value: Any):
        self.__categories = value

    def __fill_options(self) -> None:
        assert self.categories is not None
        self.add_option(label=_("Back"), emoji=PartialEmoji(name='left', id=1033551843210579988), value="shake_back")
        for Group in self.categories.keys():
            value = getattr(Group, 'qualified_name', str(Group))
            self.find[value] = Group

            label = getattr(Group, 'label', '<LABEL NOT FOUND>')
            emoji = getattr(Group, "display_emoji", None)
            description = (getattr(Group, 'description', '').split("\n", 1)[0] or None) if getattr(Group, 'describe', True) else None
            
            self.add_option(label=label, value=value, description=description, emoji=emoji)


    async def callback(self, interaction: Interaction):
        assert self.view is not None
        assert self.categories is not None
        value = self.values[0]
        if value == "shake_back":
            if isinstance(self.view.source, FrontPageSource):
                if self.view.page == 0:
                    await interaction.response.defer()
                    await utils.maybe_coroutine(self.view.on_stop, interaction=interaction)
                else:
                    await self.view.rebind(self.view.front(), 0, interaction=interaction)  
            else:
                await self.view.rebind(self.view.front(), interaction=interaction)
        else:
            group = self.find.get(value, MISSING)
            items = self.categories.get(group, MISSING)
            if group == MISSING or items == MISSING:
                await interaction.response.send_message(_("This category either does not exist or has no items for you."), ephemeral=True)
                return
            source = self.source(ctx=self.ctx, group=group, items=items, interaction=interaction)
            self.view.cache['source'] = self.view.cache['page'] = None
            await self.view.rebind(source, interaction=interaction)
