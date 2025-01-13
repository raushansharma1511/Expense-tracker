from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .serializers import CategorySerializer
from .models import Category


class CategoriesView(APIView):
    """view to create and list categories"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve predefined and user-specific categories.
        """
        if request.user.is_staff:
            # if user is staff then show them all the available categories
            categories = Category.objects.filter(is_deleted=False)
            serializer = CategorySerializer(categories, many=True)

            response_data = serializer.data

        else:
            # Retrieve predefined categories
            predefined_categories = Category.objects.filter(
                is_predefined=True, is_deleted=False
            )
            predefined_serializer = CategorySerializer(predefined_categories, many=True)

            # Retrieve user-specific categories
            user_categories = Category.objects.filter(
                user=request.user, is_deleted=False
            )
            user_serializer = CategorySerializer(user_categories, many=True)

            response_data = {
                "predefined_categories": predefined_serializer.data,
                "user_categories": user_serializer.data,
            }

        return Response(
            {
                "message": "Categories retrieved successfully.",
                "data": response_data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Add user sepecific category
        """
        serializer = CategorySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            if request.user.is_staff:
                # is user is staff user then catagory is predefined
                serializer.save(user=request.user, is_predefined=True)
            else:
                serializer.save(user=request.user)  # Associate category with the user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriesDetailView(APIView):
    """Api View to update, view and delete specific category"""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        """Method to get a specific category object by its id."""
        try:
            category = Category.objects.get(pk=pk, is_deleted=False)

            # Check if the user is the owner or is a staff member
            if category.user == request.user or request.user.is_staff:
                return category
            else:
                # Return a proper response for permission denied
                raise PermissionDenied("You don't have access to this category.")
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        Retrieve a specific category by its ID.
        """
        try:
            category = Category.objects.get(id=pk, is_deleted=False)

            if (
                category.user == request.user
                or category.is_predefined
                or request.user.is_staff
            ):
                serializer = CategorySerializer(category)
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(
                {"error": "Access denied to this category."},
                status=status.HTTP_403_FORBIDDEN,
            )

        except Category.DoesNotExist:
            return Response(
                {"error": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request, pk):
        """
        Fully update a specific category. Requires all parameters to be passed in the request.
        """
        category = self.get_object(pk, request)
        if category:
            # If the category is found and user has permission, update it
            serializer = CategorySerializer(
                category, data=request.data, context={"request": request}
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"error": "Category not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def delete(self, request, pk):
        """
        delete a specific category.
        """
        category = self.get_object(pk, request)
        if category:
            category.is_deleted = True  # Perform a soft delete
            category.save()  # Save the updated category object
            return Response(
                {"message": "Category deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"error": "Category not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )
