#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    # ------------------------------------------------inventory order

    path('inventory_order/new_item/create/<order_id>/', views.InventoryOrderNewItemEditView.as_view(),
         name='inventory_order_new_item_create'),
    path('inventory_order/new_item/edit/<int:pk>/', views.InventoryOrderNewItemEditView.as_view(),
         name='inventory_order_new_item_edit'),
    path('inventory_order/new_item/delete/<int:pk>/', views.InventoryOrderNewItemDeleteView.as_view(),
         name='inventory_order_new_item_delete'),
    path('inventory_order/item/edit/<int:pk>/', views.InventoryOrderItemEditView.as_view(),
         name='inventory_order_item_edit'),
    path('inventory_order/item/<int:pk>/set_check/', views.InventoryOrderItemSetCheckView.as_view(),
         name='inventory_item_set_check'),
    path('inventory_order/<int:pk>/delete/', views.InventoryOrderDeleteView.as_view(), name='inventory_order_delete'),
    path('inventory_order/<int:pk>/update/', views.InventoryOrderUpdateView.as_view(), name='inventory_order_update'),
    path('inventory_order/create/', views.InventoryOrderCreateView.as_view(), name='inventory_order_create'),
    path('inventory_order/<int:pk>/', views.InventoryOrderDetailView.as_view(), name='inventory_order_detail'),
    path('inventory_order/', views.InventoryOrderListView.as_view(), name='inventory_order_list'),
    # ------------------------------------------------turn back

    path('turn_back/item/delete/<int:pk>', views.TurnBackOrderItemDeleteView.as_view(),
         name='turn_back_order_item_delete'),
    path('turn_back/update/<int:pk>/', views.TurnBackOrderUpdateView.as_view(), name='turn_back_order_update'),
    path('turn_back/delete/<int:pk>/', views.TurnBackOrderDeleteView.as_view(), name='turn_back_order_delete'),
    path('turn_back/<model_name>/<from_order_id>/', views.TurnBackOrderCreateView.as_view(),
         name='turn_back_order_create'),
    path('turn_back/<int:pk>/', views.TurnBackOrderDetailView.as_view(), name='turn_back_order_detail'),

    # ------------------------------------------------expenses

    path('expenses_item_update/<int:pk>/', views.MrpExpenseItemUpdateView.as_view(),
         name='expenses_item_update'),
    path('expenses_item_create/', views.MrpExpenseItemCreateView.as_view(),
         name='expenses_item_create'),
    path('expenses_item/', views.MrpExpensesItemListView.as_view(),
         name='expenses_item_list'),
    path('expenses_item_delete/<int:pk>/', views.MrpExpenseDeleteView.as_view(),
         name='mrp_item_expenses_delete'),
    path('expenses_edit/<item_model>/<item_id>/<int:pk>/', views.MrpItemExpenseEditView.as_view(),
         name='mrp_item_expenses_edit'),
    path('expenses_create/<item_model>/<item_id>/', views.MrpItemExpenseEditView.as_view(),
         name='mrp_item_expenses_create'),
    # ------------------------------------------------move order

    path('move_order/item/create/<order_id>/', views.MoveLocationOrderItemEditView.as_view(),
         name='move_location_order_item_create'),
    path('move_order/item/<int:pk>/edit/', views.MoveLocationOrderItemEditView.as_view(),
         name='move_location_order_item_edit'),
    path('move_order/item/<int:pk>/delete/', views.MoveLocationOrderItemDeleteView.as_view(),
         name='move_location_order_item_delete'),
    path('move_order/<int:pk>/update/', views.MoveLocationOrderUpdateView.as_view(), name='move_location_order_update'),
    path('move_order/<int:pk>/pdf/', views.MoveOrderToPdfView.as_view(), name='move_order_pdf'),
    path('move_order/<int:pk>/delete/', views.MoveLocationOrderDeleteView.as_view(), name='move_location_order_delete'),
    path('move_order/create/', views.MoveLocationOrderCreateView.as_view(), name='move_location_order_create'),
    path('move_wh_order/create/<type>/', views.MoveLocationOrderCreateView.as_view(), name='move_location_order_create'),
    path('move_order/<int:pk>/', views.MoveLocationOrderDetailView.as_view(), name='move_location_order_detail'),
    path('move_wh_order/', views.MoveWarehouseOrderListView.as_view(), name='move_warehouse_order_list'),
    path('move_order/day-daily/', views.MoveLocationOrderDayListView.as_view(), name='move_location_order_day_daily_list'),
    path('move_order/', views.MoveLocationOrderListView.as_view(), name='move_location_order_list'),

    # ------------------------------------------------production order
    path('production/produce_item/create/<order_id>/<item_id>/', views.ProductionOrderProduceItemEditView.as_view(),
         name='production_produce_item_create'),
    path('production/produce_item/delete/<int:pk>/', views.ProductionOrderProduceItemDeleteView.as_view(),
         name='production_produce_item_delete'),
    path('production/produce_item/edit/<int:pk>/', views.ProductionOrderProduceItemEditView.as_view(),
         name='production_produce_item_edit'),
    path('production/raw_item/delete/<int:pk>/', views.ProductionOrderRawItemDeleteView.as_view(),
         name='production_raw_item_delete'),
    path('production/raw_item/edit/<int:pk>/', views.ProductionOrderRawItemEditView.as_view(),
         name='production_raw_item_edit'),
    path('production/raw_item/create/<order_id>/', views.ProductionOrderRawItemEditView.as_view(),
         name='production_raw_item_create'),
    path('production/update/<int:pk>/', views.ProductionOrderUpdateView.as_view(), name='production_update'),
    path('production/create/', views.ProductionOrderCreateView.as_view(), name='production_create'),
    path('production/<int:pk>/', views.ProductionOrderDetailView.as_view(), name='production_detail'),
    path('production/day-daily/', views.ProductionOrderDayListView.as_view(), name='production_day_daily_list'),
    path('production/', views.ProductionOrderListView.as_view(), name='production_list'),
    # ------------------------------------------------production type
    path('production_type/update/<int:pk>', views.ProductionTypeUpdateView.as_view(), name='production_type_update'),
    path('production_type/create/', views.ProductionTypeCreateView.as_view(), name='production_type_create'),
    path('production_type/<int:pk>/', views.ProductionTypeDetailView.as_view(), name='production_type_detail'),
    path('production_type/', views.ProductionTypeListView.as_view(), name='production_type_list'),
    # ------------------------------------------------In Out Order

    path('in_order/purchase_order/create/<int:purchase_order_id>/', views.PurchaseOrderInOrderCreateView.as_view(),
         name='purchase_order_in_order'),
    path('out_order/sales_order/<int:sales_order_id>/', views.SalesOrderInOrderCreateView.as_view(),
         name='sales_order_out_order'),
    path('in_out_order/item/delete/<int:pk>/', views.InOutOrderItemDeleteView.as_view(), name='in_out_order_item_delete'),
    path('in_out_order/item/create/<order_id>/', views.InOutOrderItemEditView.as_view(),
         name='in_out_order_item_create'),
    path('in_out_order/item/edit/<int:pk>/', views.InOutOrderItemEditView.as_view(), name='in_out_order_item_edit'),
    path('in_out_order/delete/<int:pk>/', views.InOutOrderDeleteView.as_view(), name='in_out_order_delete'),
    path('in_out_order/<int:pk>/', views.InOutOrderDetailView.as_view(), name='in_out_order_detail'),
    path('in_out_order/day-daily/', views.InOutOrderDayListView.as_view(), name='in_out_order_day_daily_list'),
    path('in_out_order/', views.InOutOrderListView.as_view(), name='in_out_order_list'),
    path('supplier/update/<int:pk>/', views.SupplierUpdateView.as_view(), name='pro_ser_supplier_update'),
    path('supplier/create/', views.SupplierCreateView.as_view(), name='pro_ser_supplier_create'),
    path('supplier/<int:pk>', views.MrpSupplierDetailView.as_view(), name='pro_ser_supplier_detail'),
    path('supplier/', views.MrpSupplierListView.as_view(), name='pro_ser_supplier_list'),
]
