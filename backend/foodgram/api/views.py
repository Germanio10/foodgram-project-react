from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from users.models import User, Subscribe
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart
from .serializers import (UserReadSerializer, UserCreateSerializer,
                          SetPasswordSerializer, TagsReadSerializer,
                          IngredientsReadSerializer, RecipeReadSerializer,
                          SubscribeSerializer, RecipeFavoriteSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipeShoppingCartCreateSerializer)
from rest_framework.permissions import AllowAny
from .pagination import CustomPaginator
from rest_framework import mixins, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .filters import RecipeFilter
import csv
from django.http import HttpResponse
from .permissions import IsAuthorOrReadOnly
from django.db.models import Sum


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny, )
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        else:
            return UserCreateSerializer

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Пароль успешно изменен'},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])
        user = request.user
        if request.method == 'POST':
            if author == request.user:
                return Response(
                    {'error': 'Нельзя подписываться на самого себя'})
            serilizer = SubscribeSerializer(author, data=request.data,
                                            context={'request': request})
            serilizer.is_valid(raise_exception=True)
            Subscribe.objects.get_or_create(author=author, user=user)
            return Response(serilizer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            Subscribe.objects.filter(author=author, user=user).delete()
            return Response({'detail': 'Вы отписались'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated, ),
            pagination_class=CustomPaginator)
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(page, many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)


class TagsViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsReadSerializer
    permission_classes = [AllowAny, ]
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsReadSerializer
    permission_classes = [AllowAny, ]
    pagination_class = None
    search_fields = ('^name', )
    filter_backends = (filters.SearchFilter, )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [AllowAny, ]
    pagination_class = CustomPaginator
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete', 'create']

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [AllowAny]
        elif self.action in ['retrieve', 'create']:
            permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            permission_classes = [IsAuthorOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeReadSerializer
        else:
            return RecipeCreateUpdateSerializer

    @action(detail=True, permission_classes=(IsAuthenticated, ),
            methods=['post', 'delete'])
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe):
                return Response(
                    {"error": "Рецепт уже есть в избранном"}
                )
            serializer = RecipeFavoriteSerializer(recipe, data=request.data,
                                                  context={'request': request})
            serializer.is_valid(raise_exception=True)
            Favorite.objects.create(recipe=recipe, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not Favorite.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                return Response(
                    {"error": "Рецепта нет в избранном"}
                    )
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response({'detail': 'Рецепт удален из избранного'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, permission_classes=(IsAuthenticated, ),
            methods=['post', 'delete'], pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe):
                return Response(
                    {"error": "Рецепт уже в списках покупок"}
                )
            serializer = RecipeShoppingCartCreateSerializer(recipe,
                                                            data=request.data,
                                                            context={'request':
                                                                     request})
            serializer.is_valid(raise_exception=True)
            ShoppingCart.objects.create(recipe=recipe,
                                        user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(recipe=recipe,
                                               user=request.user).exists():
                return Response(
                    {"error": "Рецепта нет в списках покупок"}
                )
            ShoppingCart.objects.filter(recipe=recipe,
                                        user=request.user).delete()
            return Response(
                {'detail': 'Рецепт удален из списка покупок'}
            )

    @action(detail=False, permission_classes=(IsAuthenticated, ),
            methods=['get'])
    def download_shopping_cart(self, request, **kwargs):
        shopping_cart = (
            request.user.shopping_user
            .values('recipe__name', 'recipe__recipes__ingredient__name')
            .annotate(amount=Sum('recipe__recipes__amount'))
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.csv"'
        writer = csv.writer(response)
        writer.writerow(['Recipe', 'Ingredient', 'Amount'])

        for item in shopping_cart:
            writer.writerow([item['recipe__name'], item['recipe__recipes__ingredient__name'], item['amount']])

        return response
