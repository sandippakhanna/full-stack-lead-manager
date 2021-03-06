from rest_framework import permissions, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Lead, Developer


class LeadList(APIView):
    class LeadSerializer(serializers.ModelSerializer):
        class Meta:
            model = Lead
            fields = ("id", "title", "description")

    def get(self, request, format=None):
        user = request.user
        queryset = Lead.objects.filter(user=user)
        serializer = self.LeadSerializer(queryset, many=True)
        return Response(data={"success": True, "data": serializer.data})

    def post(self, request, format=None):
        data = request.data
        user = request.user

        title = data.get("title")
        description = data.get("description")
        clientName = data.get("clientName")
        clientEmail = data.get("clientEmail")
        clientPhone = data.get("clientPhone")

        # validation
        if title is None:
            return Response(
                {"success": False, "error": "`title` should not be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if clientName is None:
            return Response(
                {"success": False, "error": "`clientName` should not be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead = Lead.objects.create(
            user=user,
            title=title,
            description=description,
            clientName=clientName,
            clientEmail=clientEmail,
            clientPhone=clientPhone,
        )

        serializer = self.LeadSerializer(instance=lead)

        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED
        )


# Detail List View & edit
class LeadDetail(APIView):
    class LeadSerializer(serializers.ModelSerializer):
        class Meta:
            model = Lead
            fields = (
                "id",
                "title",
                "description",
                "clientName",
                "clientName",
                "clientEmail",
                "clientPhone",
            )

    def get(self, request, pk, format=None):
        user = request.user

        try:
            lead = Lead.objects.get(user=user, pk=pk)
            serializer = self.LeadSerializer(instance=lead)
            data = serializer.data
            return Response({"success": True, "data": data})

        except Lead.DoesNotExist:
            return Response(
                {"success": False, "error": "Lead is not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, pk, format=None):
        user = request.user

        try:
            lead = Lead.objects.get(user=user, pk=pk)
            serializer = self.LeadSerializer(
                instance=lead, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "data": serializer.data})
            else:
                return Response(
                    {"success": False, "error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Lead.DoesNotExist:
            return Response(
                {"success": False, "error": "Lead is not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request, pk, format=None):
        user = request.user

        try:
            lead = Lead.objects.get(user=user, pk=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Lead.DoesNotExist:
            return Response(
                {"success": False, "error": "Lead is not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )


# Developer get & Create
class DeveloperList(APIView):
    class DeveloperSerializer(serializers.ModelSerializer):
        class Meta:
            model = Developer
            fields = ("id", "name", "email", "phone")

    def get(self, request, format=None):
        user = request.user

        developers = Developer.objects.filter(user=user)
        serializer = self.DeveloperSerializer(instance=developers, many=True)

        return Response({"success": True, "data": serializer.data})

    def post(self, request, format=None):
        user = request.user
        data = request.data

        serializer = self.DeveloperSerializer(data=data)
        if serializer.is_valid():
            developer = Developer.objects.create(
                user=user,
                name=serializer.data["name"],
                email=serializer.data["email"],
                phone=serializer.data["phone"],
            )
            serializer = self.DeveloperSerializer(instance=developer)

            return Response(
                {"success": True, "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"success": False, "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DeveloperDelete(APIView):
    def delete(self, request, pk, format=None):
        try:
            developer = Developer.objects.get(user=request.user, id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Developer.DoesNotExist:
            return Response(
                data={"success": False, "error": "Developer does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )


# Developer Add to a lead
class DeveloperLead(APIView):
    class DeveloperSerializer(serializers.ModelSerializer):
        class Meta:
            model = Developer
            fields = ("id", "name", "email", "phone")

    def get(self, request, pk, format=None):
        data = request.data

        try:
            lead = Lead.objects.get(user=request.user, id=pk)
            serializer = self.DeveloperSerializer(
                instance=lead.developers.all(), many=True
            )

            unassignedDevelopers = self.DeveloperSerializer(
                instance=lead.unAssignedDevelopers(), many=True
            )

            return Response(
                {
                    "success": True,
                    "data": {
                        "assigned": serializer.data,
                        "unassigned": unassignedDevelopers.data,
                    },
                }
            )

        except Lead.DoesNotExist:
            return Response({"success": False, "error": "Lead not found"})

    def post(self, request, pk, format=None):
        data = request.data

        developerId = data.get("developerId")
        leadId = pk

        # validation
        if developerId is None:
            return Response(
                {"success": False, "error": "`developerId` field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if type(developerId) != int:
            return Response(
                {"success": False, "error": "`developerId` field is an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lead = Lead.objects.get(user=request.user, id=leadId)
        except Lead.DoesNotExist:
            return Response(
                {"success": False, "error": "Lead does't exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            developer = Developer.objects.get(user=request.user, id=developerId)
        except Developer.DoesNotExist:
            return Response(
                {"success": False, "error": "Developer does't exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Add the developer into the lead
        if developer in lead.developers.all():
            return Response({"success": False, "error": "Developer is already added."})
        else:
            lead.developers.add(developer)

            return Response(
                {"success": True, "message": "Developer is added into the lead."}
            )

    def delete(self, request, pk, format=None):
        data = request.data

        developerId = data.get("developerId")
        leadId = pk

        # validation
        if developerId is None:
            return Response(
                {"success": False, "error": "`developerId` field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if type(developerId) != int:
            return Response(
                {"success": False, "error": "`developerId` field is an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lead = Lead.objects.get(user=request.user, id=leadId)
        except Lead.DoesNotExist:
            return Response(
                {"success": False, "error": "Lead does't exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            developer = Developer.objects.get(user=request.user, id=developerId)
        except Developer.DoesNotExist:
            return Response(
                {"success": False, "error": "Developer does't exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Add the developer into the lead
        if developer not in lead.developers.all():
            return Response({"success": False, "error": "Developer is not there."})
        else:
            lead.developers.remove(developer)

            return Response(
                {"success": True, "message": "Developer is removed from the lead."}
            )
