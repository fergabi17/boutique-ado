from django.shortcuts import render, redirect, reverse, get_object_or_404
from .models import Product, Category
from .forms import ProductForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.functions import Lower

# Create your views here.
def all_products(request):
    """ A view to show all products, including sorting and searching queries """
    
    products = Product.objects.all()
    query = None
    categories = None
    sort = None
    direction = None
    
    if request.GET:
        if 'sort' in request.GET:
            sort_key = request.GET['sort']
            sort = sort_key
            
            if sort_key == 'name':
                sort_key = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))
                
            if sort_key == 'category':
                sort_key = 'category__name'
                
            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sort_key = f'-{sort_key}'
            products = products.order_by(sort_key)
        
        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)
            categories = Category.objects.filter(name__in=categories)
        
        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "You didn't enter any search criteria!")
                return redirect(reverse('products'))
            
            queries = Q(name__icontains=query) | Q(description__icontains=query)
            products = products.filter(queries)
    
    current_sorting = f'{sort}_{direction}'
    
    context = {
        'products': products,
        'search_term': query,
        'current_categories': categories,
        'current_sorting': current_sorting
    }
    
    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """ A view to show individual product details """
    
    product = get_object_or_404(Product, pk=product_id)
    
    context = {
        'product': product
    }
    
    return render(request, 'products/product_detail.html', context)


@login_required
def add_product(request):
    """
    Add a product to the store
    """
    if not request.user.is_superuser():
        messages.error(request, "Sorry, only store owners can do that")
        return redirect(reverse('home'))
    else:
        if request.method == "POST":
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.save()
                messages.success(request, "Successfully added the product")
                return redirect(reverse('product_detail', args=[product.id]))
            else:
                messages.error(request, "Please ensure the form is valid")
        else:
            form = ProductForm()
        template = "products/add_product.html"
        context= {
            'form': form
        }
        return render(request, template, context)


@login_required
def edit_product(request, product_id):
    """
    Edit a product in the store
    """
    if not request.user.is_superuser():
        messages.error(request, "Sorry, only store owners can do that")
        return redirect(reverse('home'))
    else:
        product = get_object_or_404(Product, pk=product_id)
        if request.method == "POST":
            form = ProductForm( request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, "Product updated")
                return redirect(reverse('product_detail', args=[product.id]))
            else:
                messages.error(request, "There was a problem with your form")
        else:
            form = ProductForm(instance=product)
        messages.info(request, f'You are editing {product.name}')
        template = "products/edit_product.html"
        context= {
            'form': form,
            'product': product
        }
        
        return render(request, template, context)


@login_required
def delete_product(request, product_id):
    """
    Deletes a product 
    """
    if not request.user.is_superuser():
        messages.error(request, "Sorry, only store owners can do that")
        return redirect(reverse('home'))
    else:
        product = get_object_or_404(Product, pk=product_id)
        product.delete()
        messages.success(request, "Product deleted")
        return redirect(reverse("products"))