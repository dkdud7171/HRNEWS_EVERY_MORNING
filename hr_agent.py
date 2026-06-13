#!/usr/bin/env python3
"""
Daily HR News Agent
Fetches HR-related news and sends them via email using Google Gemini processing
"""

import os
import sys
import requests
import smtplib
import google.generativeai as genai
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
    Process news items with Google Gemini to generate summary
    
    Args:
        news_items: List of news items from Naver
        
    Returns:
        Processed summary text
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("Error: GOOGLE_API_KEY not set")
        return ""
    
    genai.configure(api_key=api_key)

    # Candidate models to try (order = preferred -> fallback)
    candidate_models = [
        "gemini-1.5-flash-002",
        "gemini-1.5-flash",
        "gemini-1.5-mini",
        "text-bison-001",
    ]

    # Format news for processing
    news_text = "\n".join([
        f"- {item['title']}: {item.get('description','') or item.get('title','')}"
        for item in news_items
    ])

    prompt = (
        "You are an HR news summarizer. Please summarize the following HR-related news in Korean, "
        "highlighting key insights and trends. Make the summary clear and well-organized.\n\n"
        f"HR News:\n{news_text}\n\nPlease provide a comprehensive summary of the news."
    )

    last_err = None
    for mname in candidate_models:
        try:
            print(f"Trying model: {mname}")
            model = genai.GenerativeModel(mname)
            response = model.generate_content(prompt)
            # Some clients return .text, others return .content; handle both
            if hasattr(response, "text"):
                return response.text
            if hasattr(response, "content"):
                return response.content
            # Fallback: string conversion
            return str(response)
        except Exception as e:
            print(f"Model {mname} failed: {e!r}")
            last_err = e

    print(f"Error processing with Google Gemini: all candidate models failed. Last error: {last_err!r}")
    return ""


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
    print("\n2. Processing news with Google Gemini...")
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
