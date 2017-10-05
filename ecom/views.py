# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render,render_to_response, get_object_or_404, redirect
from .models import *
from .models import Product
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Q

from .cart import Cart
from .forms import CartAddProductForm

import re

from .forms import CategoryForm , ProductForm, CustomerDetailForm
from django.contrib.auth.decorators import user_passes_test, login_required

from django.views.decorators.http import require_POST


def index(request):
    cart = Cart(request)
    categories=Category.objects.all()
    products=Product.objects.all()[:4]
    productstwo = Product.objects.all()[8:10]
    featured = Product.objects.all()[10:13]
    productsnext = Product.objects.all()[4:8]
    context = {
     'products':products,
     'productstwo':productstwo,
     'featured':featured,
     'productsnext':productsnext,
     'categories':categories,
     'cart':cart,
     }
    return render(request,'frontend/index.html', context)

def categoryview(request, pk):
	categories=Category.objects.all()
	category=Category.objects.get(pk=pk)
	products = Product.objects.filter(Categories = category)
	return render(request,'frontend/category.html', {'products':products, 'categories':categories })


#search box
def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

def get_query(query_string, search_fields):
    query = None
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query

def search(request):
    categories=Category.objects.all()
    found_entries = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        entry_query = get_query(query_string, [ 'Name',])

        found_entries = Product.objects.filter(entry_query)

    return render_to_response('frontend/search.html',
                          { 'query_string': query_string, 'found_entries': found_entries, 'categories':categories},
                          )


def product_detail(request, pk):
    categories=Category.objects.all()
    post=get_object_or_404(Product, pk=pk)
    no = int(post.NumbersAvailable)+1
    cart_product_form = CartAddProductForm()
    return render(request,'frontend/single.html', {'post': post, 'cart_product_form':CartAddProductForm, 'categories':categories, "range":range(1,no)})


def categoryview(request, pk):
    categories=Category.objects.all()
    category=Category.objects.get(pk=pk)
    products = Product.objects.filter(Categories = category)
    return render(request,'frontend/category.html', {'products':products, 'categories':categories})


def thankyou(request):
    return render(request,'frontend/pay.html', {})

def finalthnx(request):
    return render(request,'frontend/thanku.html', {})
	

def aboutus(request):
	return render(request,'frontend/aboutus.html', {})

def privacy(request):
	return render(request,'frontend/privacy.html', {})

def terms(request):
	return render(request,'frontend/terms.html', {})

def info(request):
	return render(request,'frontend/info.html', {})	
	
	


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'], update_quantity=cd['update'])
    return redirect('cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')


def cart_detail(request):
    categories=Category.objects.all()
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'update': True})
    return render(request, 'frontend/detail.html', {'cart': cart, 'categories':categories})


@login_required
def checkout(request, pk=None):
    try:
        usr = User.objects.get(pk=pk)
    except:
        usr = None
    try:
        cdet = CustomerDetail.objects.get(user=usr)
    except:
        cdet = None
    cart = Cart(request)
    if request.method=="POST":
        form=CustomerDetailForm(request.POST, instance = cdet)
        if form.is_valid():
            post=form.save(commit=False)
            post.user = usr
            post.save()
            ord = Order.objects.create(user=post, totalamount =int(cart.get_total_price()), checkout_date= timezone.now())
            for i in cart:
                c = Cartm.objects.create(order = ord, product = i["product"], quantity = int(i["quantity"]), amount = int(i["price"]))
                p = Product.objects.get(id = i["product"].id )
                p.NumbersAvailable-=int(i["quantity"])
                p.save()
            cart.clear()
            return redirect('thankyou')
    else:
        form=CustomerDetailForm(instance = cdet)
    return render(request,'frontend/checkout.html',{'form':form})


@user_passes_test(lambda u:u.is_superuser)
def dashcategory(request):
	items=Category.objects.all()
	return render(request,'backend/category.html' ,{'items':items})

@user_passes_test(lambda u:u.is_superuser)
def dashproduct(request):
	items=Product.objects.all()
	return render(request,'backend/products.html' ,{'items':items})


@user_passes_test(lambda u:u.is_superuser)
def addcategory(request):
	form=CategoryForm()
	if request.method=="POST":
		form=CategoryForm(request.POST)
		if form.is_valid():
			post=form.save(commit=False)
			post.save()
	return render(request,'backend/addcategory.html' ,{'form':form})

@user_passes_test(lambda u:u.is_superuser)
def addproduct(request):
	form=ProductForm()
	if request.method=="POST":
		form=ProductForm(request.POST)
		if form.is_valid():
			post=form.save(commit=False)
			post.save()
	return render(request,'backend/addproduct.html',{'form':form})

@user_passes_test(lambda u:u.is_superuser)
def user_detail(request):
    users= User.objects.filter(is_superuser = False)
    return render(request,'backend/user_detail.html',{'users':users})

def saletime():
    sal = []
    days = []
    sal5 = []
    today = timezone.now()
    toda = today.date()
    li = [toda-timedelta(i) for i in range(20)]
    for i in li:
        k = Order.objects.filter(checkout_date__date = i).count()
        c = User.objects.filter(date_joined__date = i).count()
        sal.append(k)
        sal5.append(k+5)
        days.append(i.day)
    sal.reverse()
    days.reverse()
    return sal, sal5, days

@user_passes_test(lambda u:u.is_superuser)
def salesreport(request):
    orders= Order.objects.all()
    sal, sal5, days = saletime()
    return render(request,'backend/salesreport.html',{'orders':orders,
                                                      'sal': sal,
                                                      'sal5': sal5,
                                                      'days': days,
                                                        })

@user_passes_test(lambda u:u.is_superuser)
def orderdet(request, pk):
    order=Order.objects.get(pk=pk)
    items = Cartm.objects.filter(order=order)
    return render(request,'backend/orderdetails.html' ,{'order':order, 'items':items})

@user_passes_test(lambda u:u.is_superuser)
def product_del(request, pk):
    product = Product.objects.get(pk=pk)
    product.delete()
    items=Product.objects.all()
    return redirect("dashproduct")

def timetime():
    sal = []
    cust = []
    today = timezone.now()
    toda = today.date()
    li = [toda-timedelta(i) for i in range(7)]
    for i in li:
        k = Order.objects.filter(checkout_date__date = i).count()
        c = User.objects.filter(date_joined__date = i).count()
        cust.append([i.day,c])
        sal.append([i.day,k])
    return sal, cust


@user_passes_test(lambda u:u.is_superuser)
def dashboard(request):
    admin = request.user
    sales = Order.objects.all().count()
    customers = User.objects.all().count()-1
    prods = Product.objects.all().count()
    sal, cust = timetime()
    return render(request, "backend/index.html", {'admin':admin,
                                                  'sales':sales,
                                                  'customers': customers,
                                                  'prods': prods,
                                                  'sal':sal,
                                                  'cust':cust,
                                                    })


