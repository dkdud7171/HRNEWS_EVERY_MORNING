#!/usr/bin/env python3
"""
Daily HR News Agent
Fetches HR-related news and sends them via email using OpenAI processing
"""

import os
import sys
import time
import traceback
import requests
import smtplib
from openai import OpenAI
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_naver_news(keyword: str, display: int = 10) -> list:
    """
    Fetch news from Naver News API
    
    Args:
        keyword: Search keyword
        display: Number of results to display
        
    Returns:
        List of news items
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: NAVER_CLIENT_ID or NAVER_CLIENT_SECRET not set")
        return []
    
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.RequestException as e:
        print(f"Error fetching news: {e}")
        return []


def process_news_with_ai(news_items: list) -> str:
    """
    Process news items with OpenAI to generate summary
    
    Args:
        news_items: List of news items from Naver
        
    Returns:
        Processed summary text
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return ""

    client = OpenAI(api_key=api_key)

    # Format news for processing
    news_text = "\n".join([
        f"- {item['title']}: {item.get('description','') or item.get('title','')}"
        for item in news_items
    ])

    messages = [
        {
            "role": "system",
            "content": "You are an HR news summarizer. Summarize the following HR-related news in Korean, highlighting key insights and trends."
        },
        {
            "role": "user",
            "content": f"Please summarize the following HR news:\n\n{news_text}"
        }
    ]

    # Retry with exponential backoff for transient errors (rate limits, network)
    max_retries = 3
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_exc = e
            err_text = str(e)
            print(f"Attempt {attempt} - OpenAI call failed: {err_text}")
            # If it's clearly a quota/billing issue, stop retrying early
            if "insufficient_quota" in err_text or "quota" in err_text:
                print("Insufficient quota or billing issue detected. Check your OpenAI plan and billing settings.")
                break
            if attempt < max_retries:
                sleep_sec = 2 ** (attempt - 1)
                print(f"Retrying in {sleep_sec}s...")
                time.sleep(sleep_sec)
            else:
                print("Max retries reached.")

    print("All OpenAI attempts failed. Falling back to a local summary.")
    print("Last exception:\n", traceback.format_exception_only(type(last_exc), last_exc))
    return local_fallback_summary(news_items)


def local_fallback_summary(news_items: list) -> str:
    """
    Simple local summarizer used when the AI provider is unavailable.
    Returns a concise bullet list of titles + first sentence of description in Korean.
    """
    bullets = []
    for item in news_items:
        title = item.get("title", "(제목 없음)")
        desc = item.get("description", "") or ""
        # take up to first 200 chars to keep it short
        short = desc.replace('\n', ' ').strip()
        if len(short) > 200:
            short = short[:197].rsplit(' ', 1)[0] + '...'
        bullets.append(f"- {title}: {short}")
    header = "(자동 폴백 요약) 아래는 원문 제목과 간단한 설명입니다:\n\n"
    return header + "\n".join(bullets)


def send_email(subject: str, body: str) -> bool:
    """
    Send email with the processed news
    
    Args:
        subject: Email subject
        body: Email body (HTML or plain text)
        
    Returns:
        True if successful, False otherwise
    """
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")
    
    if not all([sender, password, receiver]):
        print("Error: Email configuration not set properly")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = receiver
        
        # Attach HTML version
        part = MIMEText(body, "html", "utf-8")
        msg.attach(part)
        
        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        
        print(f"Email sent successfully to {receiver}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def format_email_body(summary: str, news_items: list) -> str:
    """
    Format the email body with HTML styling
    
    Args:
        summary: AI-processed summary
        news_items: Original news items
        
    Returns:
        Formatted HTML email body
    """
    date_str = datetime.now().strftime("%Y년 %m월 %d일")
    
    news_links = "\n".join([
        f'<li><a href="{item["link"]}">{item["title"]}</a></li>'
        for item in news_items
    ])
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>🔔 {date_str} HR 뉴스 요약</h2>
            
            <h3>📰 주요 내용</h3>
            <pre style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; white-space: pre-wrap;">{summary}</pre>
            
            <h3>📚 원문 링크</h3>
            <ul>
                {news_links}
            </ul>
            
            <hr>
            <p style="color: #666; font-size: 12px;">
                이 메일은 자동으로 생성되었습니다.
            </p>
        </body>
    </html>
    """
    return html


def main():
    """Main function to run the HR news agent"""
    print("Starting Daily HR News Agent...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Fetch HR news
    print("\n1. Fetching HR news from Naver...")
    news_items = get_naver_news("HR 인사", display=10)
    
    if not news_items:
        print("No news found. Exiting.")
        return
    
    print(f"Found {len(news_items)} news items")
    
    # Process with AI
    print("\n2. Processing news with OpenAI...")
    summary = process_news_with_ai(news_items)
    
    if not summary:
        print("Failed to process news. Exiting.")
        return
    
    print("Summary generated successfully")
    
    # Format and send email
    print("\n3. Preparing and sending email...")
    email_body = format_email_body(summary, news_items)
    subject = f"[HR News] {datetime.now().strftime('%Y-%m-%d')} 일일 뉴스 요약"
    
    if send_email(subject, email_body):
        print("✅ Process completed successfully!")
    else:
        print("❌ Failed to send email")
        sys.exit(1)


if __name__ == "__main__":
    main()
