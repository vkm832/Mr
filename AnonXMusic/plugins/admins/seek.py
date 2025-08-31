# Add these callback handlers to your callback file (usually in callbacks.py or admins/callback.py)

from pyrogram import filters
from pyrogram.types import CallbackQuery
from AnonXMusic import app
from AnonXMusic.core.call import Anony
from AnonXMusic.misc import db
from AnonXMusic.utils import AdminRightsCheck, seconds_to_min
from AnonXMusic.utils.inline import close_markup
from config import BANNED_USERS


@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@AdminRightsCheck
async def admin_callback(cli, callback_query: CallbackQuery, _, chat_id):
    command = callback_query.data.split()[1]
    
    # Handle seek forward 10 seconds
    if command == "Seek10":
        await handle_seek(callback_query, chat_id, 10, False, _)
    
    # Handle seek forward 20 seconds
    elif command == "Seek20":
        await handle_seek(callback_query, chat_id, 20, False, _)
    
    # Handle seek backward 10 seconds
    elif command == "SeekBack10":
        await handle_seek(callback_query, chat_id, 10, True, _)
    
    # Handle seek backward 20 seconds
    elif command == "SeekBack20":
        await handle_seek(callback_query, chat_id, 20, True, _)


async def handle_seek(callback_query, chat_id, seconds, is_backward, _):
    """Handle seeking forward or backward"""
    try:
        playing = db.get(chat_id)
        if not playing:
            return await callback_query.answer(_["queue_2"], show_alert=True)
        
        duration_seconds = int(playing[0]["seconds"])
        if duration_seconds == 0:
            return await callback_query.answer(_["admin_22"], show_alert=True)
        
        file_path = playing[0]["file"]
        duration_played = int(playing[0]["played"])
        duration = playing[0]["dur"]
        
        if is_backward:
            # Seek backward
            if (duration_played - seconds) <= 10:
                return await callback_query.answer(
                    f"Cannot seek backward. Current position: {seconds_to_min(duration_played)}/{duration}",
                    show_alert=True
                )
            to_seek = duration_played - seconds + 1
        else:
            # Seek forward
            if (duration_seconds - (duration_played + seconds)) <= 10:
                return await callback_query.answer(
                    f"Cannot seek forward. Current position: {seconds_to_min(duration_played)}/{duration}",
                    show_alert=True
                )
            to_seek = duration_played + seconds + 1
        
        # Handle different file types
        if "vid_" in file_path:
            from AnonXMusic import YouTube
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await callback_query.answer(_["admin_22"], show_alert=True)
        
        check = (playing[0]).get("speed_path")
        if check:
            file_path = check
        
        if "index_" in file_path:
            file_path = playing[0]["vidid"]
        
        # Perform the seek operation
        try:
            await Anony.seek_stream(
                chat_id,
                file_path,
                seconds_to_min(to_seek),
                duration,
                playing[0]["streamtype"],
            )
        except Exception as e:
            return await callback_query.answer("Failed to seek. Try again.", show_alert=True)
        
        # Update the played time in database
        if is_backward:
            db[chat_id][0]["played"] -= seconds
        else:
            db[chat_id][0]["played"] += seconds
        
        # Show success message
        direction = "backward" if is_backward else "forward"
        await callback_query.answer(
            f"Seeked {direction} {seconds}s to {seconds_to_min(to_seek)}",
            show_alert=False
        )
        
    except Exception as e:
        await callback_query.answer("An error occurred while seeking.", show_alert=True)
