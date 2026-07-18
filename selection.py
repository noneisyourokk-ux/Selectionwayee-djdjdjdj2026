import requests
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Bot Configuration
BOT_TOKEN = "8254141632:AAFvRU6E4amexKzidBe2Ij9pBvkoCYozHNg"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SelectionWayBot:
    def __init__(self):
        self.base_headers = {
            "sec-ch-ua-platform": "\"Windows\"",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            "content-type": "application/json",
            "sec-ch-ua-mobile": "?0",
            "accept": "*/*",
            "origin": "https://www.selectionway.com",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.selectionway.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i"
        }
        self.user_sessions = {}
        # Dynamic API configurations (Node logic integration)
        self.DYNAMIC_BASE_URL = "https://backend.multistreaming.site/api"
        self.DEFAULT_EXTRACTOR_USER_ID = "3708939"

    def clean_url(self, url):
        """Clean URL by removing spaces"""
        if not url:
            return ""
        return url.replace(" ", "%20")

    async def get_all_batches(self):
        """Get all active batches without login"""
        courses_url = f"{self.DYNAMIC_BASE_URL}/courses/active?userId=1448640"
        
        courses_headers = {
            "host": "backend.multistreaming.site",
            **self.base_headers
        }
        
        try:
            session = requests.Session()
            response = session.get(courses_url, headers=courses_headers)
            response.raise_for_status()
            
            courses_response = response.json()
            if courses_response.get("state") == 200:
                return True, courses_response["data"]
            else:
                return False, "Failed to get batches"
                
        except Exception as e:
            return False, f"Error: {str(e)}"

    async def get_my_batches(self, user_id):
        """Get user's own batches after login"""
        if user_id not in self.user_sessions:
            return False, "Please login first"
        
        user_data = self.user_sessions[user_id]
        courses_url = f"{self.DYNAMIC_BASE_URL}/courses/my-courses"
        
        courses_headers = {
            "host": "backend.multistreaming.site",
            "content-length": "20",
            **self.base_headers
        }
        
        courses_data = {
            "userId": str(user_data['user_id'])
        }
        
        try:
            response = user_data['session'].post(courses_url, headers=courses_headers, json=courses_data)
            response.raise_for_status()
            
            courses_response = response.json()
            if courses_response.get("state") == "200":
                return True, courses_response["data"]
            else:
                return False, "Failed to get your courses"
                
        except Exception as e:
            return False, f"Error: {str(e)}"

    async def login_user(self, email, password, user_id):
        """Login to SelectionWay"""
        login_url = "https://selectionway.hranker.com/admin/api/user-login"
        
        login_headers = {
            "host": "selectionway.hranker.com",
            "content-length": "106",
            **self.base_headers
        }
        
        login_data = {
            "email": email,
            "password": password,
            "mobile": "",
            "otp": "",
            "logged_in_via": "web",
            "customer_id": 561
        }
        
        try:
            session = requests.Session()
            response = session.post(login_url, headers=login_headers, json=login_data)
            response.raise_for_status()
            
            login_response = response.json()
            if login_response.get("state") == 200:
                user_data = {
                    'user_id': login_response["data"]["user_id"],
                    'token': login_response["data"]["token_id"],
                    'session': session
                }
                self.user_sessions[user_id] = user_data
                return True, "✅ Login successful!"
            else:
                return False, "❌ Login failed: Invalid credentials"
                
        except Exception as e:
            return False, f"❌ Login error: {str(e)}"

    async def deep_extract_node_pdfs(self, batch_id):
        """
        [INTEGRATED NODE LOGIC]
        Bina login ke batch -> subjects -> topics ke andar se pure PDFs nikalne ke liye loop.
        """
        deep_pdfs = []
        user_id = self.DEFAULT_EXTRACTOR_USER_ID
        
        try:
            # 1. Get Subjects
            subjects_url = f"{self.DYNAMIC_BASE_URL}/subjects?batchId={batch_id}&userId={user_id}&limit=1000"
            res = requests.get(subjects_url, headers=self.base_headers)
            if res.status_code != 200:
                return []
            subjects = res.json().get("data", [])
            
            # 2. Loop through Subjects to get Topics
            for sub in subjects:
                sub_id = sub.get("id") or sub.get("_id")
                sub_name = sub.get("name", "Unknown Subject")
                
                topics_url = f"{self.DYNAMIC_BASE_URL}/topics?subjectId={sub_id}&batchId={batch_id}&userId={user_id}&limit=1000"
                t_res = requests.get(topics_url, headers=self.base_headers)
                if t_res.status_code != 200:
                    continue
                topics = t_res.json().get("data", [])
                
                # 3. Loop through Topics to get PDFs
                for topic in topics:
                    topic_id = topic.get("id") or topic.get("_id")
                    topic_name = topic.get("name", "Unknown Topic")
                    
                    pdfs_url = f"{self.DYNAMIC_BASE_URL}/pdfs?topicId={topic_id}&subjectId={sub_id}&batchId={batch_id}&userId={user_id}&limit=1000"
                    p_res = requests.get(pdfs_url, headers=self.base_headers)
                    if p_res.status_code != 200:
                        continue
                    pdfs = p_res.json().get("data", [])
                    
                    # 4. Extract URLs (Clean spaces)
                    for pdf in pdfs:
                        pdf_url = pdf.get("url") or pdf.get("pdfUrl") or pdf.get("link")
                        if pdf_url:
                            pdf_title = pdf.get("name") or pdf.get("title") or "Document"
                            clean_lnk = self.clean_url(pdf_url)
                            deep_pdfs.append(f"[{sub_name}] -> {topic_name} -> {pdf_title} : {clean_lnk}")
        except Exception as e:
            logger.error(f"Deep PDF extraction error: {str(e)}")
            
        return deep_pdfs

    async def extract_course_data_without_login(self, course_id, course_name):
        """Extract course data without login"""
        try:
            classes_url = f"{self.DYNAMIC_BASE_URL}/courses/{course_id}/classes?populate=full"
            classes_headers = {
                "host": "backend.multistreaming.site",
                **self.base_headers
            }
            
            session = requests.Session()
            response = session.get(classes_url, headers=classes_headers)
            response.raise_for_status()
            
            classes_response = response.json()
            if classes_response.get("state") == 200:
                all_batches_success, all_batches = await self.get_all_batches()
                pdf_url = ""
                
                if all_batches_success:
                    for batch in all_batches:
                        if batch.get('id') == course_id:
                            pdf_url = self.clean_url(batch.get('batchInfoPdfUrl', ""))
                            break
                
                # Dynamic Deep PDF Scan call kiya
                deep_pdf_links = await self.deep_extract_node_pdfs(course_id)
                
                return True, {
                    "classes_data": classes_response["data"],
                    "pdf_url": pdf_url,
                    "deep_pdfs": deep_pdf_links,
                    "course_details": {"title": course_name}
                }
            else:
                return False, "Failed to get course data"
                
        except Exception as e:
            return False, f"Error: {str(e)}"

    async def extract_course_data_with_login(self, user_id, course_id, course_name):
        """Extract course data with login"""
        if user_id not in self.user_sessions:
            return False, "Please login first!"
        
        user_data = self.user_sessions[user_id]
        
        course_url = f"{self.DYNAMIC_BASE_URL}/courses/by-id-2"
        course_headers = {
            "host": "backend.multistreaming.site",
            "content-length": "52",
            **self.base_headers
        }
        
        course_data = {
            "userId": str(user_data['user_id']),
            "id": course_id
        }
        
        try:
            response = user_data['session'].post(course_url, headers=course_headers, json=course_data)
            course_response = response.json()
            
            if course_response.get("state") != 200:
                return False, "Failed to get course details"
            
            course_details = course_response["data"]
            pdf_url = self.clean_url(course_details.get("batchInfoPdfUrl", ""))
            
            classes_url = f"{self.DYNAMIC_BASE_URL}/courses/{course_id}/classes?populate=full"
            classes_headers = {
                "host": "backend.multistreaming.site",
                **self.base_headers
            }
            
            response = user_data['session'].get(classes_url, headers=classes_headers)
            response.raise_for_status()
            
            classes_response = response.json()
            if classes_response.get("state") == 200:
                # Login ke sath bhi Deep Dynamic loop run hoga extra material ke liye
                deep_pdf_links = await self.deep_extract_node_pdfs(course_id)
                
                return True, {
                    "classes_data": classes_response["data"],
                    "pdf_url": pdf_url,
                    "deep_pdfs": deep_pdf_links,
                    "course_details": course_details
                }
            else:
                return False, "Failed to get course data"
                
        except Exception as e:
            return False, f"Error: {str(e)}"

    def format_batches_list(self, courses_data, list_type="all"):
        """Format batches list for display"""
        if not courses_data:
            return "No batches found!", []
        
        if list_type == "all":
            message = "📚 *All Available Batches*\n\n"
        else:
            message = "📚 *Your Batches*\n\n"
        
        batch_list = []
        
        if list_type == "all":
            for course in courses_data:
                batch_list.append(course)
        else:
            for course_group in courses_data:
                live_courses = course_group.get("liveCourses", [])
                recorded_courses = course_group.get("recordedCourses", [])
                for course in live_courses + recorded_courses:
                    batch_list.append(course)
        
        if not batch_list:
            return "❌ No batches found!", []
        
        for i, course in enumerate(batch_list, 1):
            title = course.get('title', 'Unknown')
            course_id = course.get('id', 'N/A')
            price = course.get('discountPrice', course.get('price', 'N/A'))
            category = course.get('mainCategory', {}).get('mainCategoryName', 'General')
            course_type = "🔴 LIVE" if course.get('isLive') else "📹 RECORDED"
            
            message += f"*{i}. {title}*\n"
            message += f"   🆔 `{course_id}`\n"
            message += f"   📁 {category}\n"
            message += f"   💰 ₹{price} | {course_type}\n"
            message += f"   📖 {course.get('short_description', 'No description')}\n\n"
        
        if list_type == "my":
            message += "👉 Reply with batch number to extract (e.g., `1`)"
        else:
            message += "👉 Reply with *batch ID* to extract (e.g., `68ce5fe8bb3c8f24bb3d4f77`)"
        
        return message, batch_list

    def extract_all_data(self, classes_data, pdf_url, deep_pdfs, course_details):
        """Extract all data from course including Deep Node PDFs"""
        video_links = []
        pdf_links = []
        
        if pdf_url:
            pdf_links.append(f"Batch Info PDF : {pdf_url}")
            
        # Add deep scanned PDFs from Node logic
        if deep_pdfs:
            pdf_links.extend(deep_pdfs)
        
        if classes_data and "classes" in classes_data:
            for topic_group in classes_data["classes"]:
                for class_item in topic_group.get("classes", []):
                    title = class_item.get("title", "Unknown Title")
                    mp4_recordings = class_item.get("mp4Recordings", [])
                    
                    best_url = None
                    best_quality = ""
                    
                    for recording in mp4_recordings:
                        quality = recording.get("quality", "")
                        url = recording.get("url", "")
                        
                        if quality == "720p":
                            best_url = url
                            best_quality = "720p"
                            break
                        elif quality == "480p" and not best_url:
                            best_url = url
                            best_quality = "480p"
                        elif quality == "360p" and not best_url:
                            best_url = url
                            best_quality = "360p"
                    
                    if not best_url:
                        best_url = class_item.get("class_link", "")
                        best_quality = "YouTube"
                    
                    if best_url:
                        video_links.append(f"{title}({best_quality}) : {best_url}")
        
        return video_links, pdf_links

    def create_course_file(self, course_name, video_links, pdf_links):
        """Create course file with modern format"""
        clean_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{clean_name.replace(' ', '_')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"🎯 {course_name}\n\n")
            
            if pdf_links:
                f.write("📄 PDF FILES & IN-DEPTH STUDY MATERIAL:\n")
                for pdf in pdf_links:
                    f.write(f"{pdf}\n")
                f.write("\n")
            
            if video_links:
                f.write("🎥 VIDEO LINKS:\n")
                for video in video_links:
                    f.write(f"{video}\n")
        
        return filename

bot = SelectionWayBot()

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔐 Login & Extract", callback_data="login_extract")],
        [InlineKeyboardButton("📚 List All Batches", callback_data="list_batches")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *SelectionWay Extractor Bot*\n\nChoose an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "login_extract":
        context.user_data['awaiting_login'] = True
        context.user_data['action_type'] = 'login_extract'
        await query.edit_message_text(
            "🔐 *Login Required*\n\n"
            "Please send your login credentials in this format:\n"
            "`email:password`\n\n"
            "Example:\n"
            "`9007111119:Ty28@`",
            parse_mode='Markdown'
        )
    elif query.data == "list_batches":
        await query.edit_message_text("🔄 Loading all batches...")
        success, result = await bot.get_all_batches()
        if success:
            batches_list, batch_list = bot.format_batches_list(result, "all")
            context.user_data['all_batches'] = batch_list
            context.user_data['awaiting_batch_id'] = True
            context.user_data['action_type'] = 'all_batches'
            await query.edit_message_text(batches_list, parse_mode='Markdown')
        else:
            await query.edit_message_text(f"❌ {result}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    if context.user_data.get('awaiting_login'):
        if ":" in text:
            email, password = text.split(":", 1)
            await update.message.reply_text("🔄 Logging in...")
            success, message = await bot.login_user(email.strip(), password.strip(), user_id)
            if success:
                context.user_data['awaiting_login'] = False
                await update.message.reply_text("🔄 Loading your batches...")
                success, my_batches = await bot.get_my_batches(user_id)
                if success:
                    formatted_list, batch_list = bot.format_batches_list(my_batches, "my")
                    context.user_data['my_batches'] = batch_list
                    context.user_data['awaiting_batch_selection'] = True
                    await update.message.reply_text(formatted_list, parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"✅ Login successful but {my_batches}")
            else:
                await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Invalid format! Please use:\n`email:password`", parse_mode='Markdown')
            
    elif context.user_data.get('awaiting_batch_selection'):
        if text.isdigit():
            batch_number = int(text)
            batch_list = context.user_data.get('my_batches', [])
            if 1 <= batch_number <= len(batch_list):
                selected_batch = batch_list[batch_number - 1]
                course_id = selected_batch.get('id')
                course_name = selected_batch.get('title', 'Course')
                
                await update.message.reply_text(f"⏳ Extracting *{course_name}* along with in-depth PDFs...", parse_mode='Markdown')
                success, result = await bot.extract_course_data_with_login(user_id, course_id, course_name)
                if success:
                    await process_extraction_result(update, course_name, result)
                    context.user_data['awaiting_batch_selection'] = False
                else:
                    await update.message.reply_text(f"❌ {result}")
            else:
                await update.message.reply_text(f"❌ Please enter a number between 1 and {len(batch_list)}")
        else:
            await update.message.reply_text("❌ Please enter a valid number")
            
    elif context.user_data.get('awaiting_batch_id'):
        batch_id = text.strip()
        batch_list = context.user_data.get('all_batches', [])
        course_name = "Unknown Course"
        for batch in batch_list:
            if batch.get('id') == batch_id:
                course_name = batch.get('title', 'Unknown Course')
                break
                
        await update.message.reply_text(f"⏳ Deep scanning PDFs & videos for *{course_name}*...", parse_mode='Markdown')
        success, result = await bot.extract_course_data_without_login(batch_id, course_name)
        if success:
            await process_extraction_result(update, course_name, result)
            context.user_data['awaiting_batch_id'] = False
        else:
            await update.message.reply_text(f"❌ {result}")
            
    elif text.startswith('/'):
        await update.message.reply_text("Please use /start to begin")

async def process_extraction_result(update, course_name, result):
    """Cleaned and Fixed: Process extraction result and send file"""
    video_links, pdf_links = bot.extract_all_data(
        result["classes_data"], 
        result["pdf_url"],
        result.get("deep_pdfs", []),
        result["course_details"]
    )
    
    filename = bot.create_course_file(course_name, video_links, pdf_links)
    
    caption = (
        f"🎯 *{course_name}*\n\n"
        f"📊 *Extraction Complete!*\n"
        f"• 🎥 Total Videos: {len(video_links)}\n"
        f"• 📄 Total PDFs Found: {len(pdf_links)}\n"
        f"• 📦 File: `{filename}`\n\n"
        f"✅ *All links are ready to use!*"
    )
    
    with open(filename, 'rb') as f:
        await update.message.reply_document(
            document=f,
            filename=filename,
            caption=caption,
            parse_mode='Markdown'
        )
    try:
        os.remove(filename)
    except:
        pass

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(login_extract|list_batches)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Bot is running perfectly with deep PDF extractor...")
    application.run_polling()

if __name__ == '__main__':
    main()