"""stone URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.static import serve

from django.conf.urls import url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from django.urls import include

from django.views.i18n import JavaScriptCatalog

from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    # 导入 admin。widget需要的url
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('cart/', include('cart.urls')),
    path('product/', include('product.urls')),
    path('purchase/', include('purchase.urls')),
    path('partner/', include('partner.urls')),
    path('stock/', include('stock.urls')),
    path('invoice/', include('invoice.urls')),
    path('mrp/', include('mrp.urls')),
    path('sales/', include('sales.urls')),
    path('files/', include('files.urls')),
    path('comment/', include('comment.urls')),
    path('wechat/', include('action.urls')),
    path('tasks/', include('tasks.urls')),
    path('ratings/', include('star_ratings.urls', namespace='ratings')),
    path('', RedirectView.as_view(url='account/dashboard/')),
    # selectable
]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# if settings.DEBUG:
#     urlpatterns += staticfiles_urlpatterns()
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# import debug_toolbar
# urlpatterns += [
#     url(r'^__debug__/', include(debug_toolbar.urls)),
# ]

# if settings.DEBUG is False:
#     # urlpatterns += patterns('',
#     #         url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT,
#     #        }),
#     #     )
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
