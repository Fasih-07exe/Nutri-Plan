from django.shortcuts import render
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import json
import os 
import random
from django.views.decorators.http import require_POST
from django.http import JsonResponse

@require_POST
def swap_meal(request):
    index = int(request.POST.get('index'))
    user = request.session.get('user')
    current_meals = request.session.get('meals', [])
    goal = user['goal']
    diet_type = user['diet_type']

    # Load meals
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE_DIR, 'meals.json'), 'r') as f:
        all_meals = json.load(f)

    filtered = [
        meal for meal in all_meals
        if (meal['type'] == diet_type or diet_type == 'any') and goal in meal['goal']
        and meal not in current_meals  # avoid duplicates
    ]

    if not filtered:
        return JsonResponse({'error': 'No more meals available'}, status=400)

    new_meal = random.choice(filtered)
    current_meals[index] = new_meal
    request.session['meals'] = current_meals

    return JsonResponse({'meal': new_meal})

def generate_diet_plan(goal, diet_type):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE_DIR, 'meals.json'), 'r') as f:
        data = json.load(f)
        # print(type(data))

    meals =data

    # Filter meals by diet_type and goal
    filtered_meals = [
        meal for meal in meals
        if (meal['type'] == diet_type or diet_type == 'any')
        and (goal in meal['goal'])
    ]

    # If less than 3 meals available, just return all
    if len(filtered_meals) < 3:
        selected_meals = filtered_meals
    else:
        # Randomly select 3 meals
        selected_meals = random.sample(filtered_meals, 3)

    # Build shopping list from selected meals
    shopping_items = {}
    for meal in selected_meals:
        for ing in meal['ingredients']:
            if ing['name'] not in shopping_items:
                shopping_items[ing['name']] = ing['quantity']

    shopping_list = [{'name': name, 'details': qty} for name, qty in shopping_items.items()]

    return selected_meals, shopping_list


class DietPlanPDFView:
    def __init__(self, user, meals, shopping_list):
        self.user = user
        self.meals = meals
        self.shopping_list = shopping_list

    def generate_pdf(self):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, f"Diet Plan for {self.user['name']}")
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Goal: {self.user['goal'].title()}")
        p.drawString(50, height - 100, f"Diet Type: {self.user['diet_type'].title()}")

        y = height - 140
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Recommended Meals:")
        y -= 20

        p.setFont("Helvetica", 12)
        for meal in self.meals:
            p.drawString(60, y, f"- {meal['name']} ({meal['calories']} cal)")
            y -= 15
            for ing in meal['ingredients']:
                line = f"    * {ing['name']}: {ing['quantity']} ({ing['instructions']})"
                p.drawString(70, y, line)
                y -= 15
            y -= 10
            if y < 100:
                p.showPage()
                y = height - 50

        y -= 10
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Weekly Shopping List:")
        y -= 20
        p.setFont("Helvetica", 12)
        for item in self.shopping_list:
            p.drawString(60, y, f"- {item['name']}: {item['details']}")
            y -= 15
            if y < 100:
                p.showPage()
                y = height - 50

        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


def diet_plan_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        goal = request.POST.get('goal')
        diet_type = request.POST.get('diet_type')

        user_data = {
            'name': name,
            'goal': goal,
            'diet_type': diet_type,
        }

        meals, shopping_list = generate_diet_plan(goal, diet_type)

        request.session['user'] = user_data
        request.session['meals'] = meals
        request.session['shopping_list'] = shopping_list

        return render(request, 'diet_result.html', {
            'user_name': name,
            'goal': goal,
            'diet_type': diet_type,
            'meal_options': meals,
            'shopping_list': shopping_list,
        })

    return render(request, 'diet_form.html')


def download_diet_plan(request):
    user = request.session.get('user')
    meals = request.session.get('meals')
    shopping_list = request.session.get('shopping_list')

    if not (user and meals and shopping_list):
        return HttpResponse("No diet plan data found. Please generate a diet plan first.", status=400)

    pdf_generator = DietPlanPDFView(user, meals, shopping_list)
    pdf = pdf_generator.generate_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="diet_plan.pdf"'
    response.write(pdf)
    return response

def aboutus(request):
    return render(request,"aboutus.html")