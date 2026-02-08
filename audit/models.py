from django.db import models


class AuditLog(models.Model):
	tenant = models.ForeignKey(
		"tenants.Tenant",
		on_delete=models.CASCADE,
		related_name="audit_logs",
	)
	action = models.CharField(max_length=100)
	actor = models.CharField(max_length=100)
	target = models.CharField(max_length=255)
	detail = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.action} by {self.actor}"
