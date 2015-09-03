# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Gceapi base exception handling.

Includes decorator for re-raising gceapi-type exceptions.

SHOULD include dedicated exception logging.

"""

import sys

from oslo_config import cfg
from oslo_log import log as logging

from gceapi.i18n import _
import webob.exc


LOG = logging.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='make exception message format errors fatal'),
]

CONF = cfg.CONF
CONF.register_opts(exc_log_opts)


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=0, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()


class GceapiException(Exception):
    """Base Gceapi Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))

                if CONF.fatal_exception_format_errors:
                    raise exc_info[0], exc_info[1], exc_info[2]
                else:
                    # at least get the core message out if something happened
                    message = self.msg_fmt

        super(GceapiException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full GceapiException message, (see __init__)
        return self.args[0]


class EncryptionFailure(GceapiException):
    msg_fmt = _("Failed to encrypt text: %(reason)s")


class DecryptionFailure(GceapiException):
    msg_fmt = _("Failed to decrypt text: %(reason)s")


class VirtualInterfaceCreateException(GceapiException):
    msg_fmt = _("Virtual Interface creation failed")


class VirtualInterfaceMacAddressException(GceapiException):
    msg_fmt = _("5 attempts to create virtual interface"
                "with unique mac address failed")


class GlanceConnectionFailed(GceapiException):
    msg_fmt = _("Connection to glance host %(host)s:%(port)s failed: "
        "%(reason)s")


class NotAuthorized(GceapiException):
    ec2_code = 'AuthFailure'
    msg_fmt = _("Not authorized.")
    code = 403


class AdminRequired(NotAuthorized):
    msg_fmt = _("User does not have admin privileges")


class PolicyNotAuthorized(NotAuthorized):
    msg_fmt = _("Policy doesn't allow %(action)s to be performed.")


class ImageNotActive(GceapiException):
    # NOTE(jruzicka): IncorrectState is used for volumes only in EC2,
    # but it still seems like the most appropriate option.
    ec2_code = 'IncorrectState'
    msg_fmt = _("Image %(image_id)s is not active.")


class ImageNotAuthorized(GceapiException):
    msg_fmt = _("Not authorized for image %(image_id)s.")


class Invalid(GceapiException):
    msg_fmt = _("Unacceptable parameters.")
    code = 400


class InvalidBDM(Invalid):
    msg_fmt = _("Block Device Mapping is Invalid.")


class InvalidBDMSnapshot(InvalidBDM):
    msg_fmt = _("Block Device Mapping is Invalid: "
                "failed to get snapshot %(id)s.")


class InvalidBDMVolume(InvalidBDM):
    msg_fmt = _("Block Device Mapping is Invalid: "
                "failed to get volume %(id)s.")


class InvalidBDMImage(InvalidBDM):
    msg_fmt = _("Block Device Mapping is Invalid: "
                "failed to get image %(id)s.")


class InvalidBDMBootSequence(InvalidBDM):
    msg_fmt = _("Block Device Mapping is Invalid: "
                "Boot sequence for the instance "
                "and image/block device mapping "
                "combination is not valid.")


class InvalidBDMLocalsLimit(InvalidBDM):
    msg_fmt = _("Block Device Mapping is Invalid: "
                "You specified more local devices than the "
                "limit allows")


class InvalidBDMEphemeralSize(InvalidBDM):
    msg_fmt = _("Ephemeral disks requested are larger than "
                "the instance type allows.")


class InvalidBDMSwapSize(InvalidBDM):
    msg_fmt = _("Swap drive requested is larger than instance type allows.")


class InvalidBDMFormat(InvalidBDM):
    msg_fmt = _("Block Device Mapping is Invalid: "
                "%(details)s")


class InvalidBDMForLegacy(InvalidBDM):
    msg_fmt = _("Block Device Mapping cannot "
                "be converted to legacy format. ")


class InvalidAttribute(Invalid):
    msg_fmt = _("Attribute not supported: %(attr)s")


class VolumeUnattached(Invalid):
    ec2_code = 'IncorrectState'
    msg_fmt = _("Volume %(volume_id)s is not attached to anything")


class VolumeNotCreated(GceapiException):
    msg_fmt = _("Volume %(volume_id)s did not finish being created"
                " even after we waited %(seconds)s seconds or %(attempts)s"
                " attempts.")


class InvalidKeypair(Invalid):
    ec2_code = 'InvalidKeyPair.Format'
    msg_fmt = _("Keypair data is invalid") + ": %(reason)s"


class InvalidRequest(Invalid):
    msg_fmt = _("The request is invalid.")


class InvalidInput(Invalid):
    msg_fmt = _("Invalid input received") + ": %(reason)s"


class InvalidVolume(Invalid):
    ec2_code = 'UnsupportedOperation'
    msg_fmt = _("Invalid volume") + ": %(reason)s"


class InvalidMetadata(Invalid):
    msg_fmt = _("Invalid metadata") + ": %(reason)s"


class InvalidMetadataSize(Invalid):
    msg_fmt = _("Invalid metadata size") + ": %(reason)s"


class InvalidPortRange(Invalid):
    ec2_code = 'InvalidParameterValue'
    msg_fmt = _("Invalid port range %(from_port)s:%(to_port)s. %(msg)s")


class InvalidIpProtocol(Invalid):
    msg_fmt = _("Invalid IP protocol %(protocol)s.")


class InvalidContentType(Invalid):
    msg_fmt = _("Invalid content type %(content_type)s.")


class InvalidCidr(Invalid):
    msg_fmt = _("Invalid cidr %(cidr)s.")


class InvalidUnicodeParameter(Invalid):
    msg_fmt = _("Invalid Parameter: "
                "Unicode is not supported by the current database.")


# Cannot be templated as the error syntax varies.
# msg needs to be constructed when raised.
class InvalidParameterValue(Invalid):
    ec2_code = 'InvalidParameterValue'
    msg_fmt = _("%(err)s")


class InvalidAggregateAction(Invalid):
    msg_fmt = _("Cannot perform action '%(action)s' on aggregate "
                "%(aggregate_id)s. Reason: %(reason)s.")


class InvalidGroup(Invalid):
    msg_fmt = _("Group not valid. Reason: %(reason)s")


class InvalidSortKey(Invalid):
    msg_fmt = _("Sort key supplied was not valid.")


class InstanceInvalidState(Invalid):
    msg_fmt = _("Instance %(instance_uuid)s in %(attr)s %(state)s. Cannot "
                "%(method)s while the instance is in this state.")


class InstanceNotRunning(Invalid):
    msg_fmt = _("Instance %(instance_id)s is not running.")


class InstanceNotInRescueMode(Invalid):
    msg_fmt = _("Instance %(instance_id)s is not in rescue mode")


class InstanceNotRescuable(Invalid):
    msg_fmt = _("Instance %(instance_id)s cannot be rescued: %(reason)s")


class InstanceNotReady(Invalid):
    msg_fmt = _("Instance %(instance_id)s is not ready")


class InstanceSuspendFailure(Invalid):
    msg_fmt = _("Failed to suspend instance") + ": %(reason)s"


class InstanceResumeFailure(Invalid):
    msg_fmt = _("Failed to resume instance: %(reason)s.")


class InstancePowerOnFailure(Invalid):
    msg_fmt = _("Failed to power on instance: %(reason)s.")


class InstancePowerOffFailure(Invalid):
    msg_fmt = _("Failed to power off instance: %(reason)s.")


class InstanceRebootFailure(Invalid):
    msg_fmt = _("Failed to reboot instance") + ": %(reason)s"


class InstanceTerminationFailure(Invalid):
    msg_fmt = _("Failed to terminate instance") + ": %(reason)s"


class InstanceDeployFailure(Invalid):
    msg_fmt = _("Failed to deploy instance") + ": %(reason)s"


class MultiplePortsNotApplicable(Invalid):
    msg_fmt = _("Failed to launch instances") + ": %(reason)s"


class ServiceUnavailable(Invalid):
    msg_fmt = _("Service is unavailable at this time.")


class ComputeResourcesUnavailable(ServiceUnavailable):
    msg_fmt = _("Insufficient compute resources.")


class ComputeServiceUnavailable(ServiceUnavailable):
    msg_fmt = _("Compute service of %(host)s is unavailable at this time.")


class UnableToMigrateToSelf(Invalid):
    msg_fmt = _("Unable to migrate instance (%(instance_id)s) "
                "to current host (%(host)s).")


class InvalidHypervisorType(Invalid):
    msg_fmt = _("The supplied hypervisor type of is invalid.")


class DestinationHypervisorTooOld(Invalid):
    msg_fmt = _("The instance requires a newer hypervisor version than "
                "has been provided.")


class DestinationDiskExists(Invalid):
    msg_fmt = _("The supplied disk path (%(path)s) already exists, "
                "it is expected not to exist.")


class InvalidDevicePath(Invalid):
    msg_fmt = _("The supplied device path (%(path)s) is invalid.")


class DevicePathInUse(Invalid):
    msg_fmt = _("The supplied device path (%(path)s) is in use.")
    code = 409


class DeviceIsBusy(Invalid):
    msg_fmt = _("The supplied device (%(device)s) is busy.")


class InvalidCPUInfo(Invalid):
    msg_fmt = _("Unacceptable CPU info") + ": %(reason)s"


class InvalidIpAddressError(Invalid):
    msg_fmt = _("%(address)s is not a valid IP v4/6 address.")


class InvalidVLANTag(Invalid):
    msg_fmt = _("VLAN tag is not appropriate for the port group "
                "%(bridge)s. Expected VLAN tag is %(tag)s, "
                "but the one associated with the port group is %(pgroup)s.")


class InvalidVLANPortGroup(Invalid):
    msg_fmt = _("vSwitch which contains the port group %(bridge)s is "
                "not associated with the desired physical adapter. "
                "Expected vSwitch is %(expected)s, but the one associated "
                "is %(actual)s.")


class InvalidDiskFormat(Invalid):
    msg_fmt = _("Disk format %(disk_format)s is not acceptable")


class ImageUnacceptable(Invalid):
    msg_fmt = _("Image %(image_id)s is unacceptable: %(reason)s")


class InstanceUnacceptable(Invalid):
    msg_fmt = _("Instance %(instance_id)s is unacceptable: %(reason)s")


class InvalidEc2Id(Invalid):
    msg_fmt = _("Ec2 id %(ec2_id)s is unacceptable.")


class InvalidUUID(Invalid):
    msg_fmt = _("Expected a uuid but received %(uuid)s.")


class InvalidID(Invalid):
    msg_fmt = _("Invalid ID received %(id)s.")


class ConstraintNotMet(GceapiException):
    msg_fmt = _("Constraint not met.")
    code = 412


class NotFound(GceapiException):
    msg_fmt = _("Resource could not be found.")
    code = 404


class AgentBuildNotFound(NotFound):
    msg_fmt = _("No agent-build associated with id %(id)s.")


class AgentBuildExists(GceapiException):
    msg_fmt = _("Agent-build with hypervisor %(hypervisor)s os %(os)s "
                "architecture %(architecture)s exists.")


class VolumeNotFound(NotFound):
    ec2_code = 'InvalidVolumeID.NotFound'
    msg_fmt = _("Volume %(volume_id)s could not be found.")


class SnapshotNotFound(NotFound):
    ec2_code = 'InvalidSnapshotID.NotFound'
    msg_fmt = _("Snapshot %(snapshot_id)s could not be found.")


class DiskNotFound(NotFound):
    msg_fmt = _("No disk at %(location)s")


class VolumeDriverNotFound(NotFound):
    msg_fmt = _("Could not find a handler for %(driver_type)s volume.")


class InvalidImageRef(Invalid):
    msg_fmt = _("Invalid image href %(image_href)s.")


class AutoDiskConfigDisabledByImage(Invalid):
    msg_fmt = _("Requested image %(image)s "
                "has automatic disk resize disabled.")


class ImageNotFound(NotFound):
    msg_fmt = _("Image %(image_id)s could not be found.")


# NOTE(jruzicka): ImageNotFound is not a valid EC2 error code.
class ImageNotFoundEC2(ImageNotFound):
    msg_fmt = _("Image %(image_id)s could not be found. The Gceapi EC2 API "
                "assigns image ids dynamically when they are listed for the "
                "first time. Have you listed image ids since adding this "
                "image?")


class ProjectNotFound(NotFound):
    msg_fmt = _("Project %(project_id)s could not be found.")


class StorageRepositoryNotFound(NotFound):
    msg_fmt = _("Cannot find SR to read/write VDI.")


class NetworkDuplicated(Invalid):
    msg_fmt = _("Network %(network_id)s is duplicated.")


class NetworkInUse(GceapiException):
    msg_fmt = _("Network %(network_id)s is still in use.")


class NetworkNotCreated(GceapiException):
    msg_fmt = _("%(req)s is required to create a network.")


class NetworkNotFound(NotFound):
    msg_fmt = _("Network %(network_id)s could not be found.")


class PortNotFound(NotFound):
    msg_fmt = _("Port id %(port_id)s could not be found.")


class NetworkNotFoundForBridge(NetworkNotFound):
    msg_fmt = _("Network could not be found for bridge %(bridge)s")


class NetworkNotFoundForUUID(NetworkNotFound):
    msg_fmt = _("Network could not be found for uuid %(uuid)s")


class NetworkNotFoundForCidr(NetworkNotFound):
    msg_fmt = _("Network could not be found with cidr %(cidr)s.")


class NetworkNotFoundForInstance(NetworkNotFound):
    msg_fmt = _("Network could not be found for instance %(instance_id)s.")


class NoNetworksFound(NotFound):
    msg_fmt = _("No networks defined.")


class NetworkNotFoundForProject(NotFound):
    msg_fmt = _("Either Network uuid %(network_uuid)s is not present or "
                "is not assigned to the project %(project_id)s.")


class NetworkAmbiguous(Invalid):
    msg_fmt = _("More than one possible network found. Specify "
                "network ID(s) to select which one(s) to connect to,")


class DatastoreNotFound(NotFound):
    msg_fmt = _("Could not find the datastore reference(s) which the VM uses.")


class PortInUse(Invalid):
    msg_fmt = _("Port %(port_id)s is still in use.")


class PortNotUsable(Invalid):
    msg_fmt = _("Port %(port_id)s not usable for instance %(instance)s.")


class PortNotFree(Invalid):
    msg_fmt = _("No free port available for instance %(instance)s.")


class FixedIpExists(GceapiException):
    msg_fmt = _("Fixed ip %(address)s already exists.")


class FixedIpNotFound(NotFound):
    msg_fmt = _("No fixed IP associated with id %(id)s.")


class FixedIpNotFoundForAddress(FixedIpNotFound):
    msg_fmt = _("Fixed ip not found for address %(address)s.")


class FixedIpNotFoundForInstance(FixedIpNotFound):
    msg_fmt = _("Instance %(instance_uuid)s has zero fixed ips.")


class FixedIpNotFoundForNetworkHost(FixedIpNotFound):
    msg_fmt = _("Network host %(host)s has zero fixed ips "
                "in network %(network_id)s.")


class FixedIpNotFoundForSpecificInstance(FixedIpNotFound):
    msg_fmt = _("Instance %(instance_uuid)s doesn't have fixed ip '%(ip)s'.")


class FixedIpNotFoundForNetwork(FixedIpNotFound):
    msg_fmt = _("Fixed IP address (%(address)s) does not exist in "
                "network (%(network_uuid)s).")


class FixedIpAlreadyInUse(GceapiException):
    msg_fmt = _("Fixed IP address %(address)s is already in use on instance "
                "%(instance_uuid)s.")


class FixedIpAssociatedWithMultipleInstances(GceapiException):
    msg_fmt = _("More than one instance is associated with fixed ip address "
                "'%(address)s'.")


class FixedIpInvalid(Invalid):
    msg_fmt = _("Fixed IP address %(address)s is invalid.")


class NoMoreFixedIps(GceapiException):
    ec2_code = 'UnsupportedOperation'
    msg_fmt = _("Zero fixed ips available.")


class NoFixedIpsDefined(NotFound):
    msg_fmt = _("Zero fixed ips could be found.")


class FloatingIpExists(GceapiException):
    msg_fmt = _("Floating ip %(address)s already exists.")


class FloatingIpNotFound(NotFound):
    ec2_code = "UnsupportedOpperation"
    msg_fmt = _("Floating ip not found for id %(id)s.")


class FloatingIpDNSExists(Invalid):
    msg_fmt = _("The DNS entry %(name)s already exists in domain %(domain)s.")


class FloatingIpNotFoundForAddress(FloatingIpNotFound):
    msg_fmt = _("Floating ip not found for address %(address)s.")


class FloatingIpNotFoundForHost(FloatingIpNotFound):
    msg_fmt = _("Floating ip not found for host %(host)s.")


class FloatingIpMultipleFoundForAddress(GceapiException):
    msg_fmt = _("Multiple floating ips are found for address %(address)s.")


class FloatingIpPoolNotFound(NotFound):
    msg_fmt = _("Floating ip pool not found.")
    safe = True


class NoMoreFloatingIps(FloatingIpNotFound):
    msg_fmt = _("Zero floating ips available.")
    safe = True


class FloatingIpAssociated(GceapiException):
    ec2_code = "UnsupportedOpperation"
    msg_fmt = _("Floating ip %(address)s is associated.")


class FloatingIpNotAssociated(GceapiException):
    msg_fmt = _("Floating ip %(address)s is not associated.")


class NoFloatingIpsDefined(NotFound):
    msg_fmt = _("Zero floating ips exist.")


class NoFloatingIpInterface(NotFound):
    ec2_code = "UnsupportedOpperation"
    msg_fmt = _("Interface %(interface)s not found.")


class CannotDisassociateAutoAssignedFloatingIP(GceapiException):
    ec2_code = "UnsupportedOpperation"
    msg_fmt = _("Cannot disassociate auto assigned floating ip")


class KeypairNotFound(NotFound):
    ec2_code = 'InvalidKeyPair.NotFound'
    msg_fmt = _("Keypair %(name)s not found for user %(user_id)s")


class ServiceNotFound(NotFound):
    msg_fmt = _("Service %(service_id)s could not be found.")


class ServiceBinaryExists(GceapiException):
    msg_fmt = _("Service with host %(host)s binary %(binary)s exists.")


class ServiceTopicExists(GceapiException):
    msg_fmt = _("Service with host %(host)s topic %(topic)s exists.")


class HostNotFound(NotFound):
    msg_fmt = _("Host %(host)s could not be found.")


class ComputeHostNotFound(HostNotFound):
    msg_fmt = _("Compute host %(host)s could not be found.")


class HostBinaryNotFound(NotFound):
    msg_fmt = _("Could not find binary %(binary)s on host %(host)s.")


class InvalidReservationExpiration(Invalid):
    msg_fmt = _("Invalid reservation expiration %(expire)s.")


class InvalidQuotaValue(Invalid):
    msg_fmt = _("Change would make usage less than 0 for the following "
                "resources: %(unders)s")


class QuotaNotFound(NotFound):
    msg_fmt = _("Quota could not be found")


class QuotaExists(GceapiException):
    msg_fmt = _("Quota exists for project %(project_id)s, "
                "resource %(resource)s")


class QuotaResourceUnknown(QuotaNotFound):
    msg_fmt = _("Unknown quota resources %(unknown)s.")


class ProjectUserQuotaNotFound(QuotaNotFound):
    msg_fmt = _("Quota for user %(user_id)s in project %(project_id)s "
                "could not be found.")


class ProjectQuotaNotFound(QuotaNotFound):
    msg_fmt = _("Quota for project %(project_id)s could not be found.")


class QuotaClassNotFound(QuotaNotFound):
    msg_fmt = _("Quota class %(class_name)s could not be found.")


class QuotaUsageNotFound(QuotaNotFound):
    msg_fmt = _("Quota usage for project %(project_id)s could not be found.")


class ReservationNotFound(QuotaNotFound):
    msg_fmt = _("Quota reservation %(uuid)s could not be found.")


class OverQuota(GceapiException):
    msg_fmt = _("Quota exceeded for resources: %(overs)s")


class SecurityGroupNotFound(NotFound):
    msg_fmt = _("Security group %(security_group_id)s not found.")


class SecurityGroupNotFoundForProject(SecurityGroupNotFound):
    msg_fmt = _("Security group %(security_group_id)s not found "
                "for project %(project_id)s.")


class SecurityGroupNotFoundForRule(SecurityGroupNotFound):
    msg_fmt = _("Security group with rule %(rule_id)s not found.")


class SecurityGroupExists(Invalid):
    ec2_code = 'InvalidGroup.Duplicate'
    msg_fmt = _("Security group %(security_group_name)s already exists "
                "for project %(project_id)s.")


class SecurityGroupExistsForInstance(Invalid):
    msg_fmt = _("Security group %(security_group_id)s is already associated"
                " with the instance %(instance_id)s")


class SecurityGroupNotExistsForInstance(Invalid):
    msg_fmt = _("Security group %(security_group_id)s is not associated with"
                " the instance %(instance_id)s")


class SecurityGroupDefaultRuleNotFound(Invalid):
    msg_fmt = _("Security group default rule (%rule_id)s not found.")


class SecurityGroupCannotBeApplied(Invalid):
    msg_fmt = _("Network requires port_security_enabled and subnet associated"
                " in order to apply security groups.")


class SecurityGroupRuleExists(Invalid):
    ec2_code = 'InvalidPermission.Duplicate'
    msg_fmt = _("Rule already exists in group: %(rule)s")


class NoUniqueMatch(GceapiException):
    msg_fmt = _("No Unique Match Found.")
    code = 409


class MigrationNotFound(NotFound):
    msg_fmt = _("Migration %(migration_id)s could not be found.")


class MigrationNotFoundByStatus(MigrationNotFound):
    msg_fmt = _("Migration not found for instance %(instance_id)s "
                "with status %(status)s.")


class ConsolePoolNotFound(NotFound):
    msg_fmt = _("Console pool %(pool_id)s could not be found.")


class ConsolePoolExists(GceapiException):
    msg_fmt = _("Console pool with host %(host)s, console_type "
                "%(console_type)s and compute_host %(compute_host)s "
                "already exists.")


class ConsolePoolNotFoundForHostType(NotFound):
    msg_fmt = _("Console pool of type %(console_type)s "
                "for compute host %(compute_host)s "
                "on proxy host %(host)s not found.")


class ConsoleNotFound(NotFound):
    msg_fmt = _("Console %(console_id)s could not be found.")


class ConsoleNotFoundForInstance(ConsoleNotFound):
    msg_fmt = _("Console for instance %(instance_uuid)s could not be found.")


class ConsoleNotFoundInPoolForInstance(ConsoleNotFound):
    msg_fmt = _("Console for instance %(instance_uuid)s "
                "in pool %(pool_id)s could not be found.")


class ConsoleTypeInvalid(Invalid):
    msg_fmt = _("Invalid console type %(console_type)s")


class ConsoleTypeUnavailable(Invalid):
    msg_fmt = _("Unavailable console type %(console_type)s.")


class InstanceTypeNotFound(NotFound):
    msg_fmt = _("Instance type %(instance_type_id)s could not be found.")


class InstanceTypeNotFoundByName(InstanceTypeNotFound):
    msg_fmt = _("Instance type with name %(instance_type_name)s "
                "could not be found.")


class FlavorNotFound(NotFound):
    msg_fmt = _("Flavor %(flavor_id)s could not be found.")


class FlavorAccessNotFound(NotFound):
    msg_fmt = _("Flavor access not found for %(flavor_id)s / "
                "%(project_id)s combination.")


class CellNotFound(NotFound):
    msg_fmt = _("Cell %(cell_name)s doesn't exist.")


class CellExists(GceapiException):
    msg_fmt = _("Cell with name %(name)s already exists.")


class CellRoutingInconsistency(GceapiException):
    msg_fmt = _("Inconsistency in cell routing: %(reason)s")


class CellServiceAPIMethodNotFound(NotFound):
    msg_fmt = _("Service API method not found: %(detail)s")


class CellTimeout(NotFound):
    msg_fmt = _("Timeout waiting for response from cell")


class CellMaxHopCountReached(GceapiException):
    msg_fmt = _("Cell message has reached maximum hop count: %(hop_count)s")


class NoCellsAvailable(GceapiException):
    msg_fmt = _("No cells available matching scheduling criteria.")


class CellsUpdateUnsupported(GceapiException):
    msg_fmt = _("Cannot update cells configuration file.")


class InstanceUnknownCell(NotFound):
    msg_fmt = _("Cell is not known for instance %(instance_uuid)s")


class SchedulerHostFilterNotFound(NotFound):
    msg_fmt = _("Scheduler Host Filter %(filter_name)s could not be found.")


class InstanceTypeExtraSpecsNotFound(NotFound):
    msg_fmt = _("Instance Type %(instance_type_id)s has no extra specs with "
                "key %(extra_specs_key)s.")


class FileNotFound(NotFound):
    msg_fmt = _("File %(file_path)s could not be found.")


class NoFilesFound(NotFound):
    msg_fmt = _("Zero files could be found.")


class SwitchNotFoundForNetworkAdapter(NotFound):
    msg_fmt = _("Virtual switch associated with the "
                "network adapter %(adapter)s not found.")


class NetworkAdapterNotFound(NotFound):
    msg_fmt = _("Network adapter %(adapter)s could not be found.")


class ClassNotFound(NotFound):
    msg_fmt = _("Class %(class_name)s could not be found: %(exception)s")


class NotAllowed(GceapiException):
    msg_fmt = _("Action not allowed.")


class ImageRotationNotAllowed(GceapiException):
    msg_fmt = _("Rotation is not allowed for snapshots")


class RotationRequiredForBackup(GceapiException):
    msg_fmt = _("Rotation param is required for backup image_type")


class KeyPairExists(GceapiException):
    ec2_code = 'InvalidKeyPair.Duplicate'
    msg_fmt = _("Key pair '%(key_name)s' already exists.")


class InstanceExists(GceapiException):
    msg_fmt = _("Instance %(name)s already exists.")


class InstanceTypeExists(GceapiException):
    msg_fmt = _("Instance Type with name %(name)s already exists.")


class InstanceTypeIdExists(GceapiException):
    msg_fmt = _("Instance Type with ID %(flavor_id)s already exists.")


class FlavorAccessExists(GceapiException):
    msg_fmt = _("Flavor access already exists for flavor %(flavor_id)s "
                "and project %(project_id)s combination.")


class InvalidSharedStorage(GceapiException):
    msg_fmt = _("%(path)s is not on shared storage: %(reason)s")


class InvalidLocalStorage(GceapiException):
    msg_fmt = _("%(path)s is not on local storage: %(reason)s")


class MigrationError(GceapiException):
    msg_fmt = _("Migration error") + ": %(reason)s"


class MigrationPreCheckError(MigrationError):
    msg_fmt = _("Migration pre-check error") + ": %(reason)s"


class MalformedRequestBody(GceapiException):
    msg_fmt = _("Malformed message body: %(reason)s")


# NOTE(johannes): NotFound should only be used when a 404 error is
# appropriate to be returned
class ConfigNotFound(GceapiException):
    msg_fmt = _("Could not find config at %(path)s")


class PasteAppNotFound(GceapiException):
    msg_fmt = _("Could not load paste app '%(name)s' from %(path)s")


class CannotResizeToSameFlavor(GceapiException):
    msg_fmt = _("When resizing, instances must change flavor!")


class ResizeError(GceapiException):
    msg_fmt = _("Resize error: %(reason)s")


class CannotResizeDisk(GceapiException):
    msg_fmt = _("Server disk was unable to be resized because: %(reason)s")


class InstanceTypeMemoryTooSmall(GceapiException):
    msg_fmt = _("Instance type's memory is too small for requested image.")


class InstanceTypeDiskTooSmall(GceapiException):
    msg_fmt = _("Instance type's disk is too small for requested image.")


class InsufficientFreeMemory(GceapiException):
    msg_fmt = _("Insufficient free memory on compute node to start %(uuid)s.")


class NoValidHost(GceapiException):
    msg_fmt = _("No valid host was found. %(reason)s")


class QuotaError(GceapiException):
    ec2_code = 'ResourceLimitExceeded'
    msg_fmt = _("Quota exceeded") + ": code=%(code)s"
    code = 413
    headers = {'Retry-After': 0}
    safe = True


class TooManyInstances(QuotaError):
    msg_fmt = _("Quota exceeded for %(overs)s: Requested %(req)s,"
                " but already used %(used)d of %(allowed)d %(resource)s")


class FloatingIpLimitExceeded(QuotaError):
    msg_fmt = _("Maximum number of floating ips exceeded")


class FixedIpLimitExceeded(QuotaError):
    msg_fmt = _("Maximum number of fixed ips exceeded")


class MetadataLimitExceeded(QuotaError):
    msg_fmt = _("Maximum number of metadata items exceeds %(allowed)d")


class OnsetFileLimitExceeded(QuotaError):
    msg_fmt = _("Personality file limit exceeded")


class OnsetFilePathLimitExceeded(QuotaError):
    msg_fmt = _("Personality file path too long")


class OnsetFileContentLimitExceeded(QuotaError):
    msg_fmt = _("Personality file content too long")


class KeypairLimitExceeded(QuotaError):
    msg_fmt = _("Maximum number of key pairs exceeded")


class SecurityGroupLimitExceeded(QuotaError):
    ec2_code = 'SecurityGroupLimitExceeded'
    msg_fmt = _("Maximum number of security groups or rules exceeded")


class PortLimitExceeded(QuotaError):
    msg_fmt = _("Maximum number of ports exceeded")


class AggregateError(GceapiException):
    msg_fmt = _("Aggregate %(aggregate_id)s: action '%(action)s' "
                "caused an error: %(reason)s.")


class AggregateNotFound(NotFound):
    msg_fmt = _("Aggregate %(aggregate_id)s could not be found.")


class AggregateNameExists(GceapiException):
    msg_fmt = _("Aggregate %(aggregate_name)s already exists.")


class AggregateHostNotFound(NotFound):
    msg_fmt = _("Aggregate %(aggregate_id)s has no host %(host)s.")


class AggregateMetadataNotFound(NotFound):
    msg_fmt = _("Aggregate %(aggregate_id)s has no metadata with "
                "key %(metadata_key)s.")


class AggregateHostExists(GceapiException):
    msg_fmt = _("Aggregate %(aggregate_id)s already has host %(host)s.")


class InstanceTypeCreateFailed(GceapiException):
    msg_fmt = _("Unable to create instance type")


class InstancePasswordSetFailed(GceapiException):
    msg_fmt = _("Failed to set admin password on %(instance)s "
                "because %(reason)s")
    safe = True


class DuplicateVlan(GceapiException):
    msg_fmt = _("Detected existing vlan with id %(vlan)d")


class CidrConflict(GceapiException):
    msg_fmt = _("There was a conflict when trying to complete your request.")
    code = 409


class InstanceNotFound(NotFound):
    ec2_code = 'InvalidInstanceID.NotFound'
    msg_fmt = _("Instance %(instance_id)s could not be found.")


class InstanceInfoCacheNotFound(NotFound):
    msg_fmt = _("Info cache for instance %(instance_uuid)s could not be "
                "found.")


class NodeNotFound(NotFound):
    msg_fmt = _("Node %(node_id)s could not be found.")


class NodeNotFoundByUUID(NotFound):
    msg_fmt = _("Node with UUID %(node_uuid)s could not be found.")


class MarkerNotFound(NotFound):
    msg_fmt = _("Marker %(marker)s could not be found.")


class InvalidInstanceIDMalformed(Invalid):
    ec2_code = 'InvalidInstanceID.Malformed'
    msg_fmt = _("Invalid id: %(val)s (expecting \"i-...\").")


class CouldNotFetchImage(GceapiException):
    msg_fmt = _("Could not fetch image %(image_id)s")


class CouldNotUploadImage(GceapiException):
    msg_fmt = _("Could not upload image %(image_id)s")


class TaskAlreadyRunning(GceapiException):
    msg_fmt = _("Task %(task_name)s is already running on host %(host)s")


class TaskNotRunning(GceapiException):
    msg_fmt = _("Task %(task_name)s is not running on host %(host)s")


class InstanceIsLocked(InstanceInvalidState):
    msg_fmt = _("Instance %(instance_uuid)s is locked")


class ConfigDriveInvalidValue(Invalid):
    msg_fmt = _("Invalid value for Config Drive option: %(option)s")


class ConfigDriveMountFailed(GceapiException):
    msg_fmt = _("Could not mount vfat config drive. %(operation)s failed. "
                "Error: %(error)s")


class ConfigDriveUnknownFormat(GceapiException):
    msg_fmt = _("Unknown config drive format %(format)s. Select one of "
                "iso9660 or vfat.")


class InterfaceAttachFailed(Invalid):
    msg_fmt = _("Failed to attach network adapter device to %(instance)s")


class InterfaceDetachFailed(Invalid):
    msg_fmt = _("Failed to detach network adapter device from  %(instance)s")


class InstanceUserDataTooLarge(GceapiException):
    msg_fmt = _("User data too large. User data must be no larger than "
                "%(maxsize)s bytes once base64 encoded. Your data is "
                "%(length)d bytes")


class InstanceUserDataMalformed(GceapiException):
    msg_fmt = _("User data needs to be valid base 64.")


class UnexpectedTaskStateError(GceapiException):
    msg_fmt = _("unexpected task state: expecting %(expected)s but "
                "the actual state is %(actual)s")


class InstanceActionNotFound(GceapiException):
    msg_fmt = _("Action for request_id %(request_id)s on instance"
                " %(instance_uuid)s not found")


class InstanceActionEventNotFound(GceapiException):
    msg_fmt = _("Event %(event)s not found for action id %(action_id)s")


class UnexpectedVMStateError(GceapiException):
    msg_fmt = _("unexpected VM state: expecting %(expected)s but "
                "the actual state is %(actual)s")


class CryptoCAFileNotFound(FileNotFound):
    msg_fmt = _("The CA file for %(project)s could not be found")


class CryptoCRLFileNotFound(FileNotFound):
    msg_fmt = _("The CRL file for %(project)s could not be found")


class InstanceRecreateNotSupported(Invalid):
    msg_fmt = _('Instance recreate is not implemented by this virt driver.')


class ServiceGroupUnavailable(GceapiException):
    msg_fmt = _("The service from servicegroup driver %(driver)s is "
                "temporarily unavailable.")


class DBNotAllowed(GceapiException):
    msg_fmt = _('%(binary)s attempted direct database access which is '
                'not allowed by policy')


class UnsupportedVirtType(Invalid):
    msg_fmt = _("Virtualization type '%(virt)s' is not supported by "
                "this compute driver")


class UnsupportedHardware(Invalid):
    msg_fmt = _("Requested hardware '%(model)s' is not supported by "
                "the '%(virt)s' virt driver")


class Base64Exception(GceapiException):
    msg_fmt = _("Invalid Base 64 data for file %(path)s")


class BuildAbortException(GceapiException):
    msg_fmt = _("Build of instance %(instance_uuid)s aborted: %(reason)s")


class RescheduledException(GceapiException):
    msg_fmt = _("Build of instance %(instance_uuid)s was re-scheduled: "
                "%(reason)s")


class ShadowTableExists(GceapiException):
    msg_fmt = _("Shadow table with name %(name)s already exists.")


class InstanceFaultRollback(GceapiException):
    def __init__(self, inner_exception=None):
        message = _("Instance rollback performed due to: %s")
        self.inner_exception = inner_exception
        super(InstanceFaultRollback, self).__init__(message % inner_exception)


class UnsupportedObjectError(GceapiException):
    msg_fmt = _('Unsupported object type %(objtype)s')


class OrphanedObjectError(GceapiException):
    msg_fmt = _('Cannot call %(method)s on orphaned %(objtype)s object')


class IncompatibleObjectVersion(GceapiException):
    msg_fmt = _('Version %(objver)s of %(objname)s is not supported')


class ObjectActionError(GceapiException):
    msg_fmt = _('Object action %(action)s failed because: %(reason)s')


class CoreAPIMissing(GceapiException):
    msg_fmt = _("Core API extensions are missing: %(missing_apis)s")


class AgentError(GceapiException):
    msg_fmt = _('Error during following call to agent: %(method)s')


class AgentTimeout(AgentError):
    msg_fmt = _('Unable to contact guest agent. '
                'The following call timed out: %(method)s')


class AgentNotImplemented(AgentError):
    msg_fmt = _('Agent does not support the call: %(method)s')


class InstanceGroupNotFound(NotFound):
    msg_fmt = _("Instance group %(group_uuid)s could not be found.")


class InstanceGroupIdExists(GceapiException):
    msg_fmt = _("Instance group %(group_uuid)s already exists.")


class InstanceGroupMetadataNotFound(NotFound):
    msg_fmt = _("Instance group %(group_uuid)s has no metadata with "
                "key %(metadata_key)s.")


class InstanceGroupMemberNotFound(NotFound):
    msg_fmt = _("Instance group %(group_uuid)s has no member with "
                "id %(instance_id)s.")


class InstanceGroupPolicyNotFound(NotFound):
    msg_fmt = _("Instance group %(group_uuid)s has no policy %(policy)s.")


class PluginRetriesExceeded(GceapiException):
    msg_fmt = _("Number of retries to plugin (%(num_retries)d) exceeded.")


class ImageDownloadModuleError(GceapiException):
    msg_fmt = _("There was an error with the download module %(module)s. "
                "%(reason)s")


class ImageDownloadModuleMetaDataError(ImageDownloadModuleError):
    msg_fmt = _("The metadata for this location will not work with this "
                "module %(module)s.  %(reason)s.")


class ImageDownloadModuleNotImplementedError(ImageDownloadModuleError):
    msg_fmt = _("The method %(method_name)s is not implemented.")


class ImageDownloadModuleConfigurationError(ImageDownloadModuleError):
    msg_fmt = _("The module %(module)s is misconfigured: %(reason)s.")


class PciDeviceWrongAddressFormat(GceapiException):
    msg_fmt = _("The PCI address %(address)s has an incorrect format.")


class PciDeviceNotFoundById(NotFound):
    msg_fmt = _("PCI device %(id)s not found")


class PciDeviceNotFound(GceapiException):
    msg_fmt = _("PCI Device %(node_id)s:%(address)s not found.")


class PciDeviceInvalidStatus(GceapiException):
    msg_fmt = _(
        "PCI Device %(compute_node_id)s:%(address)s is %(status)s "
        "instead of %(hopestatus)s")


class PciDeviceInvalidOwner(GceapiException):
    msg_fmt = _(
        "PCI Device %(compute_node_id)s:%(address)s is owned by %(owner)s "
        "instead of %(hopeowner)s")


class PciDeviceRequestFailed(GceapiException):
    msg_fmt = _(
        "PCI Device request (%requests)s failed")


class PciDevicePoolEmpty(GceapiException):
    msg_fmt = _(
        "Attempt to consume PCI Device %(compute_node_id)s:%(address)s "
        "from empty pool")


class PciInvalidAlias(GceapiException):
    msg_fmt = _("Invalid PCI alias definition: %(reason)s")


class PciRequestAliasNotDefined(GceapiException):
    msg_fmt = _("PCI alias %(alias)s is not defined")


class MissingParameter(GceapiException):
    ec2_code = 'MissingParameter'
    msg_fmt = _("Not enough parameters: %(reason)s")
    code = 400


class PciConfigInvalidWhitelist(Invalid):
    msg_fmt = _("Invalid PCI devices Whitelist config %(reason)s")


class PciTrackerInvalidNodeId(GceapiException):
    msg_fmt = _("Cannot change %(node_id)s to %(new_node_id)s")


# Cannot be templated, msg needs to be constructed when raised.
class InternalError(GceapiException):
    ec2_code = 'InternalError'
    msg_fmt = "%(err)s"


class PciDevicePrepareFailed(GceapiException):
    msg_fmt = _("Failed to prepare PCI device %(id)s for instance "
                "%(instance_uuid)s: %(reason)s")


class PciDeviceDetachFailed(GceapiException):
    msg_fmt = _("Failed to detach PCI device %(dev)s: %(reason)s")


class PciDeviceUnsupportedHypervisor(GceapiException):
    msg_fmt = _("%(type)s hypervisor does not support PCI devices")


class KeyManagerError(GceapiException):
    msg_fmt = _("key manager error: %(reason)s")
