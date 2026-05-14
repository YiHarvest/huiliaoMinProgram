from typing import Any, Optional

try:
    from storage import (
        delete_chat_session as delete_chat_session_sqlite,
        get_chat_message_by_uuid as get_chat_message_by_uuid_sqlite,
        get_chat_session as get_chat_session_sqlite,
        list_chat_messages as list_chat_messages_sqlite,
        list_chat_sessions as list_chat_sessions_sqlite,
        save_chat_message as save_chat_message_sqlite,
        upsert_chat_session as upsert_chat_session_sqlite,
    )
except Exception as exc:
    print(f'chat_session_storage sqlite import skipped: {exc}')
    delete_chat_session_sqlite = None
    get_chat_message_by_uuid_sqlite = None
    get_chat_session_sqlite = None
    list_chat_messages_sqlite = None
    list_chat_sessions_sqlite = None
    save_chat_message_sqlite = None
    upsert_chat_session_sqlite = None
from mysql_storage import get_mysql_connection, get_mysql_cursor, now_iso


def get_chat_session_mysql(session_uuid: str) -> Optional[dict[str, Any]]:
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    SELECT
                        session_uuid, user_id, openid, assistant_id, llm_chat_id,
                        title, preview, message_count, last_message_at,
                        deleted_at, created_at, updated_at
                    FROM ai_chat_sessions
                    WHERE session_uuid = %s
                    LIMIT 1
                    ''',
                    (session_uuid,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'sessionUuid': row[0],
                    'userId': row[1],
                    'openid': row[2],
                    'assistantId': row[3],
                    'llmChatId': row[4],
                    'title': row[5],
                    'preview': row[6],
                    'messageCount': row[7],
                    'lastMessageAt': row[8],
                    'deletedAt': row[9],
                    'createdAt': row[10],
                    'updatedAt': row[11],
                }
    except Exception as e:
        print(f'get_chat_session_mysql failed: {e}')
        return None


def upsert_chat_session_mysql(
    *,
    session_uuid: str,
    user_id: Optional[str],
    openid: str,
    assistant_id: str,
    llm_chat_id: Optional[str],
    title: str,
    preview: Optional[str],
    message_count: int,
    last_message_at: str,
    deleted_at: Optional[str] = None
) -> dict[str, Any]:
    timestamp = now_iso()
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    INSERT INTO ai_chat_sessions (
                        session_uuid, user_id, openid, assistant_id, llm_chat_id,
                        title, preview, message_count, last_message_at,
                        deleted_at, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        user_id = VALUES(user_id),
                        openid = VALUES(openid),
                        assistant_id = VALUES(assistant_id),
                        llm_chat_id = VALUES(llm_chat_id),
                        title = VALUES(title),
                        preview = VALUES(preview),
                        message_count = VALUES(message_count),
                        last_message_at = VALUES(last_message_at),
                        deleted_at = VALUES(deleted_at),
                        updated_at = VALUES(updated_at)
                    ''',
                    (
                        session_uuid,
                        user_id,
                        openid,
                        assistant_id,
                        llm_chat_id,
                        title,
                        preview,
                        message_count,
                        last_message_at,
                        deleted_at,
                        timestamp,
                        timestamp,
                    )
                )
                connection.commit()
        return get_chat_session_mysql(session_uuid) or {
            'sessionUuid': session_uuid,
            'userId': user_id,
            'openid': openid,
            'assistantId': assistant_id,
            'llmChatId': llm_chat_id,
            'title': title,
            'preview': preview,
            'messageCount': message_count,
            'lastMessageAt': last_message_at,
            'deletedAt': deleted_at,
            'createdAt': timestamp,
            'updatedAt': timestamp,
        }
    except Exception as e:
        print(f'upsert_chat_session_mysql failed: {e}')
        raise


def list_chat_sessions_mysql(
    *,
    openid: Optional[str] = None,
    user_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    limit: int = 50
) -> list[dict[str, Any]]:
    try:
        where_clauses = ['deleted_at IS NULL']
        params: list[Any] = []

        if openid:
            where_clauses.append('openid = %s')
            params.append(openid)
        elif user_id:
            where_clauses.append('user_id = %s')
            params.append(user_id)
        else:
            return []

        if assistant_id:
            where_clauses.append('assistant_id = %s')
            params.append(assistant_id)

        params.append(limit)
        sql = f'''
            SELECT
                session_uuid, user_id, openid, assistant_id, llm_chat_id,
                title, preview, message_count, last_message_at,
                deleted_at, created_at, updated_at
            FROM ai_chat_sessions
            WHERE {' AND '.join(where_clauses)}
            ORDER BY last_message_at DESC, updated_at DESC
            LIMIT %s
        '''

        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(sql, tuple(params))
                return [
                    {
                        'sessionUuid': row[0],
                        'userId': row[1],
                        'openid': row[2],
                        'assistantId': row[3],
                        'llmChatId': row[4],
                        'title': row[5],
                        'preview': row[6],
                        'messageCount': row[7],
                        'lastMessageAt': row[8],
                        'deletedAt': row[9],
                        'createdAt': row[10],
                        'updatedAt': row[11],
                    }
                    for row in cursor.fetchall()
                ]
    except Exception as e:
        print(f'list_chat_sessions_mysql failed: {e}')
        return []


def get_chat_message_mysql(message_uuid: str) -> Optional[dict[str, Any]]:
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    SELECT
                        message_uuid, session_uuid, role, message_type, content,
                        media_url, file_name, file_size, extra_json, sort_no,
                        llm_reply_id, deleted_at, created_at
                    FROM ai_chat_messages
                    WHERE message_uuid = %s
                    LIMIT 1
                    ''',
                    (message_uuid,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'messageUuid': row[0],
                    'sessionUuid': row[1],
                    'role': row[2],
                    'messageType': row[3],
                    'content': row[4],
                    'mediaUrl': row[5],
                    'fileName': row[6],
                    'fileSize': row[7],
                    'extraJson': row[8],
                    'sortNo': row[9],
                    'llmReplyId': row[10],
                    'deletedAt': row[11],
                    'createdAt': row[12],
                }
    except Exception as e:
        print(f'get_chat_message_mysql failed: {e}')
        return None


def save_chat_message_mysql(
    *,
    message_uuid: str,
    session_uuid: str,
    role: str,
    message_type: str = 'text',
    content: Optional[str] = None,
    media_url: Optional[str] = None,
    file_name: Optional[str] = None,
    file_size: Optional[int] = None,
    extra_json: Optional[str] = None,
    llm_reply_id: Optional[str] = None
) -> dict[str, Any]:
    created_at = now_iso()
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    SELECT COALESCE(MAX(sort_no), 0)
                    FROM ai_chat_messages
                    WHERE session_uuid = %s AND deleted_at IS NULL
                    ''',
                    (session_uuid,)
                )
                row = cursor.fetchone()
                next_sort = int(row[0] or 0) + 1

                cursor.execute(
                    '''
                    INSERT INTO ai_chat_messages (
                        message_uuid, session_uuid, role, message_type, content,
                        media_url, file_name, file_size, extra_json, sort_no,
                        llm_reply_id, deleted_at, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        message_uuid,
                        session_uuid,
                        role,
                        message_type,
                        content,
                        media_url,
                        file_name,
                        file_size,
                        extra_json,
                        next_sort,
                        llm_reply_id,
                        None,
                        created_at,
                    )
                )
                connection.commit()
        return get_chat_message_mysql(message_uuid) or {
            'messageUuid': message_uuid,
            'sessionUuid': session_uuid,
            'role': role,
            'messageType': message_type,
            'content': content,
            'mediaUrl': media_url,
            'fileName': file_name,
            'fileSize': file_size,
            'extraJson': extra_json,
            'sortNo': next_sort,
            'llmReplyId': llm_reply_id,
            'deletedAt': None,
            'createdAt': created_at,
        }
    except Exception as e:
        print(f'save_chat_message_mysql failed: {e}')
        raise


def list_chat_messages_mysql(
    session_uuid: str,
    *,
    include_deleted: bool = False
) -> list[dict[str, Any]]:
    try:
        sql = '''
            SELECT
                message_uuid, session_uuid, role, message_type, content,
                media_url, file_name, file_size, extra_json, sort_no,
                llm_reply_id, deleted_at, created_at
            FROM ai_chat_messages
            WHERE session_uuid = %s
        '''
        params: list[Any] = [session_uuid]
        if not include_deleted:
            sql += ' AND deleted_at IS NULL'
        sql += ' ORDER BY sort_no ASC, id ASC'

        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(sql, tuple(params))
                return [
                    {
                        'messageUuid': row[0],
                        'sessionUuid': row[1],
                        'role': row[2],
                        'messageType': row[3],
                        'content': row[4],
                        'mediaUrl': row[5],
                        'fileName': row[6],
                        'fileSize': row[7],
                        'extraJson': row[8],
                        'sortNo': row[9],
                        'llmReplyId': row[10],
                        'deletedAt': row[11],
                        'createdAt': row[12],
                    }
                    for row in cursor.fetchall()
                ]
    except Exception as e:
        print(f'list_chat_messages_mysql failed: {e}')
        return []


def delete_chat_session_mysql(session_uuid: str) -> None:
    try:
        timestamp = now_iso()
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    UPDATE ai_chat_sessions
                    SET deleted_at = %s, updated_at = %s
                    WHERE session_uuid = %s
                    ''',
                    (timestamp, timestamp, session_uuid)
                )
                connection.commit()
    except Exception as e:
        print(f'delete_chat_session_mysql failed: {e}')
        raise


def get_chat_session_sqlite_wrapper(session_uuid: str) -> Optional[dict[str, Any]]:
    return get_chat_session_sqlite(session_uuid)


def upsert_chat_session_sqlite_wrapper(**kwargs: Any) -> dict[str, Any]:
    return upsert_chat_session_sqlite(**kwargs)


def list_chat_sessions_sqlite_wrapper(**kwargs: Any) -> list[dict[str, Any]]:
    return list_chat_sessions_sqlite(**kwargs)


def save_chat_message_sqlite_wrapper(**kwargs: Any) -> dict[str, Any]:
    return save_chat_message_sqlite(**kwargs)


def list_chat_messages_sqlite_wrapper(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    return list_chat_messages_sqlite(*args, **kwargs)


def delete_chat_session_sqlite_wrapper(session_uuid: str) -> None:
    delete_chat_session_sqlite(session_uuid)
