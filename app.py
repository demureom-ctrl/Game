import flet as ft
import pyttsx3

# إعداد الصوت
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def main(page: ft.Page):
    # إعدادات شكل الصفحة
    page.title = "مساعدي الذكي"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 400

    # ماذا يحدث عند ضغط الزر
    def button_clicked(e):
        text_to_say = "مرحباً بك، لقد قمت ببناء أول تطبيق لك!"
        speak(text_to_say)
        
        # تغيير النص في الشاشة أيضاً
        t.value = "تم التحدث بنجاح ✅"
        page.update()

    # عناصر التطبيق
    t = ft.Text(value="اضغط الزر للتحدث", size=20)
    
    # --- التعديل تم هنا ---
    # لاحظ أننا كتبنا الجملة مباشرة بدون كلمة text=
    b = ft.ElevatedButton("تحدث معي", on_click=button_clicked)

    # إضافة العناصر للصفحة
    page.add(
        ft.Row([t], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([b], alignment=ft.MainAxisAlignment.CENTER),
    )

# تشغيل التطبيق
ft.app(target=main)