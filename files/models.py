import uuid

from django.db import models


class FileEntry(models.Model):
	file_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
	tenant = models.ForeignKey(
		"tenants.Tenant",
		on_delete=models.CASCADE,
		related_name="files",
	)
	name = models.CharField(max_length=255)
	relative_path = models.CharField(max_length=512)
	extension = models.CharField(max_length=32, blank=True)
	size_bytes = models.BigIntegerField(default=0)
	modified_at = models.DateTimeField()
	is_dir = models.BooleanField(default=False)
	owner = models.CharField(max_length=100, blank=True, default="system")

	class Meta:
		ordering = ["-modified_at"]

	def __str__(self) -> str:
		return f"{self.name} ({self.relative_path})"
