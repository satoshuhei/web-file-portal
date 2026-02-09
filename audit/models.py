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


class ProcessLog(models.Model):
	tenant = models.ForeignKey(
		"tenants.Tenant",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="process_logs",
	)
	job_name = models.CharField(max_length=120)
	status = models.CharField(max_length=30)
	message = models.TextField(blank=True)
	started_at = models.DateTimeField()
	finished_at = models.DateTimeField(null=True, blank=True)
	created_count = models.IntegerField(default=0)
	updated_count = models.IntegerField(default=0)
	deleted_count = models.IntegerField(default=0)
	scanned_count = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.job_name} ({self.status})"
