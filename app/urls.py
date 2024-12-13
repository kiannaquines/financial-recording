from django.urls import path
from app.views import *

urlpatterns = [
    # path('', SearchAvailable.as_view(), name='search_available'),
    path('', IndexPageView.as_view(), name='index_page'),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_user, name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # view
    path("assistance/", AssistanceView.as_view(), name="assistance"),
    path("beneficiary/", BeneficiaryView.as_view(), name="beneficiary"),
    path("client/", ClientView.as_view(), name="client"),
    path("notications/", NoticationsView.as_view(), name="notications"),
    path("users/", UsersView.as_view(), name="users"),
    path("assistance/history", AssistanceHistoryView.as_view(), name="history"),
    path('report/', GenerateReportView.as_view(), name="report"),

    path("client/family_composition/<int:pk>", FamilyCompositionView.as_view(), name="family_composition"),
    # add
    path('client/add', AddClientView.as_view(), name='add_client'),
    path('beneficiary/add', AddBeneficiaryView.as_view(), name='add_beneficiary'),
    path('assistance/add', AddAssistanceView.as_view(), name='add_assistance'),
    path('notications/add', AddNotificationView.as_view(), name='add_notications'),
    path('user/add', AddUserView.as_view(), name='add_user'),
    path('client/update/<int:pk>', UpdateClientView.as_view(), name='update_client'),
    path('beneficiary/update/<int:pk>', UpdateBeneficiaryView.as_view(), name='update_beneficiary'),
    path('assistance/update/<int:pk>', UpdateAssistanceView.as_view(), name='update_assistance'),
    path('notification/update/<int:pk>', UpdateNotificationView.as_view(), name='update_notification'),
    path('user/update/<int:pk>', UpdateUserView.as_view(), name='update_user'),
    path('client/delete/<int:pk>', RemoveClientView.as_view(), name='remove_client'),
    path('beneficiary/delete/<int:pk>', RemoveBeneficiaryView.as_view(), name='remove_beneficiary'),
    path('assistance/delete/<int:pk>', RemoveAssistanceView.as_view(), name='remove_assistance'),
    path('notification/delete/<int:pk>', RemoveNotificationView.as_view(), name='remove_notification'),
    path('user/delete/<int:pk>', RemoveUserView.as_view(), name='remove_user'),
    path('notify/', notify_client, name='notify_client'),
    path('autocomplete/', autocomplete, name='autocomplete'),


    path('senior/list', SeniorCitizenView.as_view(), name="senior_list"),
    path('sole_parent/list', SoleParentView.as_view(), name="sole_parent"),
    path('pwd/list', PWDListView.as_view(), name="pwd_list"),
]
