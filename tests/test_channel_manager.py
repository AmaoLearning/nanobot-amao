from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.manager import ChannelManager
from nanobot.config.schema import Config


def _manager() -> ChannelManager:
    cfg = Config()
    # Keep all concrete channels disabled for isolated unit tests.
    cfg.channels.send_progress = True
    cfg.channels.send_tool_hints = False
    cfg.channels.tool_hint_channels = ["feishu"]
    return ChannelManager(cfg, MessageBus())


def test_tool_hint_disabled_globally_is_blocked() -> None:
    mgr = _manager()
    msg = OutboundMessage(
        channel="feishu",
        chat_id="c1",
        content='read_file("a.txt")',
        metadata={"_progress": True, "_tool_hint": True},
    )

    assert mgr._should_deliver_outbound(msg) is False


def test_tool_hint_enabled_feishu_only() -> None:
    mgr = _manager()
    mgr.config.channels.send_tool_hints = True

    feishu_msg = OutboundMessage(
        channel="feishu",
        chat_id="c1",
        content='read_file("a.txt")',
        metadata={"_progress": True, "_tool_hint": True},
    )
    tg_msg = OutboundMessage(
        channel="telegram",
        chat_id="c2",
        content='read_file("a.txt")',
        metadata={"_progress": True, "_tool_hint": True},
    )

    assert mgr._should_deliver_outbound(feishu_msg) is True
    assert mgr._should_deliver_outbound(tg_msg) is False


def test_tool_hint_enabled_all_channels_with_wildcard() -> None:
    mgr = _manager()
    mgr.config.channels.send_tool_hints = True
    mgr.config.channels.tool_hint_channels = ["*"]

    msg = OutboundMessage(
        channel="telegram",
        chat_id="c2",
        content='exec("ls")',
        metadata={"_progress": True, "_tool_hint": True},
    )

    assert mgr._should_deliver_outbound(msg) is True


def test_reasoning_progress_respects_send_progress() -> None:
    mgr = _manager()
    msg = OutboundMessage(
        channel="feishu",
        chat_id="c1",
        content="thinking...",
        metadata={"_progress": True, "_tool_hint": False},
    )

    assert mgr._should_deliver_outbound(msg) is True

    mgr.config.channels.send_progress = False
    assert mgr._should_deliver_outbound(msg) is False


def test_non_progress_message_always_delivered() -> None:
    mgr = _manager()
    msg = OutboundMessage(channel="feishu", chat_id="c1", content="final answer")

    assert mgr._should_deliver_outbound(msg) is True
