"""    
    Django Recipes Justin Fuhrmeister-Clarke, a web-based Recipe book.
    Copyright (C) 2017  Justin Fuhrmeiser-Clarke <justin@fuhrmeister-clarke.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    """
# Create your views here.

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, FileResponse, HttpResponse, Http404, JsonResponse

from django.core.files.storage import default_storage

from django.urls import reverse
from django.forms import formset_factory

from django.conf import settings

from django.template import loader

import mimetypes
import tempfile
from shutil import copy

from .resize import createPreview, createThumbnail, createThumbnailSquare
import recipes.import_export

from .models import Category, Recipe, Ingredient
from .forms import *

def index(request):
    categories = Category.objects.all().order_by('Title')
    context = {'categories': categories,'title':getTitle()}
    return render(request, 'recipes/index.html', context)

def all(request):
    categories = Category.objects.all().order_by('Title')
    context = {'categories': categories,'title':getTitle()}
    return render(request, 'recipes/all.html', context)


def category(request, category):
    category = get_object_or_404(Category, pk=category)
    context = {'category': category,'title':getTitle()}
    return render(request, 'recipes/category.html', context)

def recipe(request, category, recipe):
    recipe = get_object_or_404(Recipe, pk=recipe)
    if( recipe.Deleted ):
        return render(request, 'recipes/index.html', {'error_message': "Unable to find Recipe.",})
        
#    ingredients=recipe.ingredient_set.all()
    context = {'recipe': recipe,'title':getTitle(recipe.Title)}
    return render(request, 'recipes/recipe.html', context)

def search(request):
    recipes=Recipe.objects.none()
    c30 = request.GET.get('c30',default=None)
    p30 = request.GET.get('p30',default=None)
    c60 = request.GET.get('c60',default=None)
    p60 = request.GET.get('p60',default=None)
    if(request.GET.get('q',default=None)):
        if(request.GET.get('title',default=None)):
            recipes = recipes.union(Recipe.objects.filter(Title__icontains=request.GET['q']))
        if(request.GET.get('method',default=None)):
            recipes = recipes.union(Recipe.objects.filter(Method__icontains=request.GET['q']),recipes)
        if(request.GET.get('notes',default=None)):
            recipes = recipes.union(Recipe.objects.filter(Notes__icontains=request.GET['q']),recipes)
        if(request.GET.get('ingredients',default=None)):
            recipes = recipes.union(Recipe.objects.filter(Ingredients__icontains=request.GET['q']),recipes)
        if(request.GET.get('serves',default="Any") != "Any"):
            serves = request.GET['serves']
            if(serves != ""):
                recipes = recipes.intersection(Recipe.objects.filter(Serves__exact=request.GET['serves']))
        
        if(p30):
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_min__lte=30))
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_min__gt=0))
            
        if(c30):
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_min__lte=30))
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_min__gt=0))
            
        if(p60):
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_min__lte=60))
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_hour__lte=1))
            
        if(c60):
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_min__lte=60))
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_hour__lte=1))
    
    if(request.GET.get('q',default=None) == 'All' and ( c30 or c60 or p30 or p60)):
        recipes=Recipe.objects.all()
        if(p30):
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_min__lte=30))
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_min__gt=0))
            
        if(c30):
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_min__lte=30))
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_min__gt=0))
            
        if(p60):
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_min__lte=60))
            #recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_min__gte=0))
            recipes = recipes.intersection(Recipe.objects.filter(Prep_Time_hour__lte=1))
            
        if(c60):
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_min__lte=60))
            #recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_min__gte=0))
            recipes = recipes.intersection(Recipe.objects.filter(Cook_Time_hour__lte=1))
    context = {'search':request.GET,'recipes':recipes,'title':getTitle("Search")}
    return render(request, 'recipes/search.html', context)


def addRecipe(request,category=-1):
    if request.method == "POST":
        recipe = RecipeForm(request.POST, request.FILES) # A form bound to the POST data
        
        
        if recipe.is_valid(): # All validation rules pass
            new_recipe = recipe.save()
            recipe = Recipe.objects.get(pk=new_recipe.id)
            image = createPreview(default_storage.location+'/'+recipe.Image.name,default_storage.location+'/'+'photo_files/thumbnails/', replace="{}.jpg".format(new_recipe.id))
            recipe.Image = image.replace(default_storage.location+'/','')
            recipe.save()
            return HttpResponseRedirect(reverse('recipes:single', args=(new_recipe.Category_id,new_recipe.id)))
    else:
        recipe = False
        recipe = RecipeForm()
        if category != -1:
            #recipe = False
            #RecipeFormSet = formset_factory(RecipeForm, extra=2)
            #recipe = RecipeFormSet(initial=[{'category':category}])
            #recipe = recipe.form
            recipe_init = Recipe()
            recipe_init.Category = Category.objects.get(pk=category)
            recipe = RecipeForm(instance=recipe_init)
        #recipe.Category = category
    context = {'request':request,'form':recipe,'category':category,'title':getTitle("Add New")}
    return render(request, 'recipes/add_edit_recipe.html',context)

def editRecipe(request, recipe):
    recipe = get_object_or_404(Recipe, pk=recipe)
    recipe_obj = recipe
    title=getTitle("Edit '" + recipe.Title +"'")
    #get ingredients:
#    ingredients = get_ingredients(request,recipe)
    if request.method == "POST":
        recipe = RecipeForm(request.POST, request.FILES, instance=recipe) # A form bound to the POST data
        if recipe.is_valid(): # All validation rules pass
            new_recipe = recipe.save()
            recipe = Recipe.objects.get(pk=new_recipe.id)
            image = createPreview(default_storage.location+'/'+recipe.Image.name,default_storage.location+'/'+'photo_files/thumbnails/', replace="{}.jpg".format(new_recipe.id))
            recipe.Image = image.replace(default_storage.location+'/','')
            recipe.save()
            #
            return HttpResponseRedirect(reverse('recipes:single', args=(new_recipe.Category_id,new_recipe.id)))
    else:
        recipe = RecipeForm(instance=recipe)
    context = {'recipe_obj': recipe_obj,'form':recipe,'title':title}
    return render(request, 'recipes/add_edit_recipe.html', context )

def thumbnail(request,recipe):
    recipe_obj = get_object_or_404(Recipe, pk=recipe)
    #photo_file = open(photo.image_file)
    #return FileResponse(photo.image_file.open())
    #return HttpResponse(content=FileResponse(open(photo.image_file.name, 'rb')),content_type=mimetypes.guess_type(photo.image_file.name)[0])
    return HttpResponse(content=FileResponse(open(default_storage.location+'/'+recipe_obj.Image.name, 'rb')),content_type=mimetypes.guess_type(recipe_obj.Image.name)[0])

def sidebyside1(request, side1):
    recipe1 = get_object_or_404(Recipe, pk=side1)
    
    if( recipe1.Deleted):
        return render(request, 'recipes/index.html', {'error_message': "Unable to find Recipe.",})
        
    title = "{} - Side".format(recipe1.Title)
    context = {'recipe1': recipe1, 'recipe2': False, 'title':getTitle()}
    return render(request, 'recipes/side1.html', context)
    
def sidebyside2(request, side1, side2):
    recipe1 = get_object_or_404(Recipe, pk=side1)
    recipe2 = get_object_or_404(Recipe, pk=side2)
    if( recipe1.Deleted or recipe2.Deleted):
        return render(request, 'recipes/index.html', {'error_message': "Unable to find Recipe.",})
        
    title = "{} - {}".format(recipe1.Title, recipe2.Title)
    context = {'recipe1': recipe1, 'recipe2': recipe2, 'title':getTitle()}
    return render(request, 'recipes/side2.html', context)
    

def sidebyside3(request, side1, side2, side3):
    recipe1 = get_object_or_404(Recipe, pk=side1)
    recipe2 = get_object_or_404(Recipe, pk=side2)
    recipe3 = get_object_or_404(Recipe, pk=side3)
    if( recipe1.Deleted or recipe2.Deleted or recipe3.Deleted):
        return render(request, 'recipes/index.html', {'error_message': "Unable to find Recipe.",})
        
    title = "{} - {} - {}".format(recipe1.Title, recipe2.Title, recipe3.Title)
    context = {'recipe1': recipe1, 'recipe2': recipe2, 'recipe3': recipe3, 'title':getTitle()}
    return render(request, 'recipes/side3.html', context)
    
    
    #ADMIN
    
def admin_home(request):
    
    context = {'title':getTitle()}
    return render(request, 'recipes/admin_home.html', context)
    
def admin_delete(request):
    all_recipes = Recipe.objects.all()
    
    if request.method == "POST":
        for recipe in all_recipes:
            
            if( request.POST.__contains__(str(recipe.id)) ):
                recipe.Deleted = True
                recipe.save()
            elif( recipe.Deleted ):
                recipe.Deleted = False
                recipe.save()
    """if request.method == "POST":
        
        for post in request.POST:
            if post == 'csrfmiddlewaretoken':
                continue
            rec = get_object_or_404(Recipe, pk=post)
            rec.Deleted = True
            rec.save()
        #recipe = RecipeForm(request.POST, request.FILES) # A form bound to the POST data
        
    else:
        pass
    """
    context = {'action':'Delete', 'recipes': all_recipes, 'title':getTitle()}
    return render(request, 'recipes/admin_delete.html', context)
    
def admin_export(request):
    all_recipes = Recipe.objects.filter(Deleted__exact=False)
    
    if request.method == "POST":
        images=False
        
        recipes_list = []
        
        for post in request.POST:
            if post == 'csrfmiddlewaretoken':
                continue
            if post == 'images':
                images=True
                continue
            else:
                recipes_list.append(post)
                
        if(images):
            with tempfile.TemporaryDirectory() as tmpdirname:
                print('created temporary directory', tmpdirname)
                recipes.import_export.export(recipes_list, tmpdirname+'/recipe export.csv')
                for recipe_id in recipes_list:
                    recipe = Recipe.objects.get(pk=recipe_id)
                    if recipe.Image:
                        copy(default_storage.location+'/'+recipe.Image.name, tmpdirname)
                with tempfile.TemporaryDirectory() as downloadtmp:
                    print('created temporary directory', downloadtmp)
                    recipes.import_export.zipdir(tmpdirname,downloadtmp+'/export.zip')
                    fsock = open(downloadtmp+'/export.zip',"rb")
                    response = HttpResponse(fsock, content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename=recipe export.zip'
                    return response
        else:
            fp = tempfile.TemporaryFile(mode='w+')
            recipes.import_export.export_download(recipes_list, fp)
            fp.seek(0)
            response = HttpResponse(fp, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=recipe export.csv'
            return response
        

    context = {'action':'Export', 'recipes': all_recipes, 'title':getTitle()}
    return render(request, 'recipes/admin_export.html', context)

def admin_import_template(request):
    
    fp = tempfile.TemporaryFile(mode='w+')
    recipes.import_export.import_template(fp)
    fp.seek(0)
    response = HttpResponse(fp, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=recipe example.csv'
    return response
    
def admin_import(request):
    
    if request.method == "POST":
        with tempfile.TemporaryDirectory() as downloadtmp:
            #------------------------------------------------------------------------------------------
            #--------TEST------------------------------------------------------------------------------
            downloadtmp='/tmp/testtmp'
            #------------------------------------------------------------------------------------------
            name='csv'
            print('created temporary directory', downloadtmp)
            for key, file in request.FILES.items():
                
                if(file.content_type == 'text/csv'):
                    name='csv'
                elif(file.content_type == 'application/zip'):
                    name='zip'
                else:
                    context = {'action':'Import', 'error_message':'Wrong File Type: only files accepted (*.zip, *.csv)', 'title':getTitle()}
                    return render(request, 'recipes/admin_import.html', context)
                dest = open(downloadtmp+'/'+name, 'wb')
                if file.multiple_chunks:
                    for c in file.chunks():
                        dest.write(c)
                else:
                    dest.write(file.read())
                dest.close()
            
            if( name == 'zip' ):
                pass

    context = {'action':'Import', 'title':getTitle()}
    return render(request, 'recipes/admin_import.html', context)
    
def import_csv(request):
    context = {}
    if request.method == "POST":
        context['imported'] = "import POST"
        file = request.files['file']
        
    else:
        context['imported' ]= "not yet ;)"
    return render(request, 'recipes/import_csv.html', context )
    

def get_import_example(request):
    return render(request, 'recipes/import_example.html')
    
def export_csv(request):
    pass
    
def get_ingredients(request,recipe):
    #recipe = get_object_or_404(Recipe, pk=recipe)
    
    ingredients=recipe.ingredient_set.values()
    return ingredients
    
def test(request, recipe):
    recipe = get_object_or_404(Recipe, pk=recipe)

    return HttpResponseRedirect(reverse('recipes:single', args=(recipe.Category_id,recipe.id)))
    
def getTitle(title=""):
    
    #string = "Recipes"
    string = ""
    try:
        string = settings.SITE_TITLE
    except:
        string = "Recipe Title"
    if(title):
        string += " - " + title
    return string
    
def ingredient_add(request):
    ingredient = IngredientForm()
    context = {'ingredient': ingredient,'form':ingredient,'title':'Ingredient Add'}
    return render(request, 'recipes/ingredients.html', context )

def category_add(request):
    category = CategoryForm()
    context = {'category': category,'form':category,'title':'Category Add'}
    return render(request, 'recipes/category_add.html', context )
    
def ingredients(request,ing_id,action):
    ingredient = get_object_or_404(Ingredient, pk=ing_id)
    title=getTitle("Edit '" + recipe.Title +"'")
    if request.method == "POST":
        ingredient = IngredientForm(request.POST,instance=recipe) # A form bound to the POST data
        if ingredient.is_valid(): # All validation rules pass
            new_ingredient = ingredient.save()
    else:
        ingredient = IngredientForm(instance=ingredient)
    context = {'ingredient': ingredient,'form':ingredient,'title':'Ingredient Edit'}
    return render(request, 'recipes/ingredients.html', context )


def categories(request,cat_id,action):
    cat = get_object_or_404(Category, pk=ing_id)
    title=getTitle("Edit '" + cat.Title +"'")
    if request.method == "POST":
        cat = IngredientForm(request.POST,instance=recipe) # A form bound to the POST data
        if cat.is_valid(): # All validation rules pass
            new_cat = cat.save()
    else:
        cat = IngredientForm(instance=recipe)
    context = {'recipe': cat,'form':cat,'title':title}
    return render(request, 'recipes/category.html', context )


#API's

def get_ing(request,recipe=-1):
    recipe = get_object_or_404(Recipe, pk=recipe)
    count=recipe.ingredient_set.count()
    error=0
    if( recipe.Deleted ):
        error=1
        data={
            'error':'Deleted'
        }
    if( not count ):
        error=1
        data={
            'error':'No Ingredients'
        }
        ingredients=recipe.ingredient_set.all()
    if( not error ):
        data={
            'ingredients':recipe.ingredient_set.all().values_list()
            }
    return JsonResponse(data)
    

def add_ing(request):
    pass

def add_cat(request):
    if request.method == "POST":
        cat = request.POST.get('new_cat','')
        if (cat == '') | (cat == 'null'):
            return JsonResponse({})
        new_cat = Category()
        new_cat.Title = request.POST.get('new_cat','')
        new_cat.save()
        data={'cat_id':new_cat.id, 
        'cat_title':new_cat.Title}
        return JsonResponse(data)

def strResp(text):
    from django.http import HttpResponse
    return HttpResponse(text)



def jsonResp(obj):
    from django.http import JsonResponse
    return JsonResponse(obj, safe=False)
