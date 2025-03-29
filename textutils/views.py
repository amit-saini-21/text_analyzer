from django.http import HttpResponse
from django.shortcuts import render
from collections import Counter
import re
import textstat
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
def home(request):
    request.session.flush()  # Pura session clear karega
    return render(request, 'index.html', {"error": ""})

def analyze(request):
    
    text = request.GET.get('text', '').strip()
    options = {
        'word_count': request.GET.get('word_count', 'off'),
        'char_count': request.GET.get('char_count', 'off'),
        'vowels_count': request.GET.get('vowels_count', 'off'),
        'longest_word': request.GET.get('longest_word', 'off'),
        'capitalize': request.GET.get('capitalize', 'off'),
        'remove_punc': request.GET.get('remove_punc', 'off'),
        'sentence_count': request.GET.get('sentence_count', 'off'),
        'frequent_word': request.GET.get('frequent_word', 'off'),
        'remove_spaces': request.GET.get('remove_spaces', 'off'),
        'complexity_score': request.GET.get('complexity_score', 'off'),
    }
    dic = {}

    # Agar text empty hai toh error do
    if not text:
        return render(request, "index.html", {"error": "Please enter some text to analyze."})

    # Agar koi checkbox select nahi hai toh error do
    if all(value == 'off' for value in options.values()):
        return render(request, "index.html", {"error": "Please select at least one option to analyze."})

    words = text.split()
    char_counter = Counter(text)  # Common Counter object use karenge
    dic['Original Text']=text
    # ✅ Word Count
    if options['word_count'] == 'on':
        word_freq = Counter(words)
        dic['Word Count'] = len(words)
        dic['Word Frequency'] = dict(sorted(word_freq.items()))

    # ✅ Character Count
    if options['char_count'] == 'on':
        chars = len(text.replace(" ", ""))  # Spaces count nahi honi chahiye
        dic['Char Count'] = chars
        dic['Char Frequency'] = dict(sorted(char_counter.items()))

    # ✅ Vowel Count
    if options['vowels_count'] == 'on':
        vowels = "aeiouAEIOU"
        vowel_count = {v: char_counter[v] for v in vowels if v in char_counter}
        dic['Total Vowels Count'] = sum(vowel_count.values())
        dic['Each Vowels Count'] = vowel_count

    # ✅ Longest Word
    if options['longest_word'] == 'on' and words:
        long = max(words, key=len)
        dic['Longest Word'] = long
        dic['Longest Word Length'] = len(long)

    # ✅ Capitalize Text
    if options['capitalize'] == 'on':
        dic['Capitialize Text'] = text.title()

    # ✅ Remove Punctuation
    if options['remove_punc'] == 'on':
        punc = '''"';:,.?{}[]()-!+-_=*&^%$#@~`<>/|\\'''
        clean_text = "".join(char for char in text if char not in punc)
        dic['Punctuations Removed'] = clean_text

    # ✅ Sentence Count
    if options['sentence_count'] == 'on':
        sentences = re.split(r'[.!?]+', text)
        dic['Total Sentence'] = len([s for s in sentences if s.strip()])

    # ✅ Frequent Word
    if options['frequent_word'] == 'on' and words:
        word_counts = Counter(words)
        most_common_word = word_counts.most_common(1)
        dic['Frequent Word'] = most_common_word[0] if most_common_word else ("None", 0)

    # ✅ Remove Extra Spaces
    if options['remove_spaces'] == 'on':
        dic['Remove Spaces'] = " ".join(text.split())

    # ✅ Complexity Score
    if options['complexity_score'] == 'on':
        score = textstat.dale_chall_readability_score(text)
        if score < 4.0:
            complexity = "Very Easy"
        elif score < 5.0:
            complexity = "Easy"
        elif score < 7.0:
            complexity = "Medium"
        else:
            complexity = "Difficult"
        dic['complexity_score'] = complexity

    # ✅ Session me Analysis Data Save Karna (PDF ke liye)
    request.session['analysis_data'] = dic

    return render(request, 'result.html', {'dic': dic})

def download_pdf(request):
    analysis_data = request.session.get('analysis_data', {})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="text_analysis.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Text Analysis Report")

    p.setFont("Helvetica", 12)
    y_position = height - 80  

    for key, value in analysis_data.items():
        value_str = str(value) if isinstance(value, (list, dict)) else str(value)

        # **Auto Line Wrap** (50 characters per line)
        wrapped_text = simpleSplit(f"{key}: {value_str}", "Helvetica", 12, width - 150)

        for line in wrapped_text:
            p.drawString(100, y_position, line)
            y_position -= 20

            # **New Page Handling**
            if y_position < 50:
                p.showPage()
                p.setFont("Helvetica", 12)
                y_position = height - 50

    p.showPage()
    p.save()
    return response

