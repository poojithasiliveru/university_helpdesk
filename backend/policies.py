
from flask import Blueprint, request, jsonify
from database import get_connection
from auth import token_required

policies = Blueprint("policies", __name__)


@policies.route("/search", methods=["GET"])
@token_required
def search_policies():

    keyword = request.args.get("q", "").strip()

    if not keyword:
        return jsonify({
            "message": "Please enter a search keyword"
        }), 400

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:
        search = f"%{keyword}%"

        cursor.execute("""
            SELECT
                p.policy_id,
                p.domain,
                p.title AS policy_title,
                p.version AS policy_version,
                p.effective_from,
                p.effective_to,
                k.article_id,
                k.title AS article_title,
                k.content AS answer,
                k.version AS article_version
            FROM policy_documents p
            JOIN knowledge_articles k
                ON p.policy_id = k.policy_id
            WHERE p.status = 'Published'
              AND CURDATE() >= p.effective_from
              AND (p.effective_to IS NULL
                   OR CURDATE() <= p.effective_to)
              AND CURDATE() >= k.effective_from
              AND (k.effective_to IS NULL
                   OR CURDATE() <= k.effective_to)
              AND (
                    p.title LIKE %s
                    OR p.policy_content LIKE %s
                    OR k.title LIKE %s
                    OR k.content LIKE %s
              )
            ORDER BY p.effective_from DESC
        """, (search, search, search, search))

        results = cursor.fetchall()

        return jsonify({
            "keyword": keyword,
            "total_results": len(results),
            "results": results
        }), 200

    except Exception as error:
        return jsonify({"message": str(error)}), 500

    finally:
        cursor.close()
        connection.close()
