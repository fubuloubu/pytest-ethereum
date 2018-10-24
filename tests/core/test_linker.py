import pytest

from ethpm import ASSETS_DIR, Package
from pytest_ethereum.deployer import Deployer
from pytest_ethereum.exceptions import DeployerError
from pytest_ethereum.linker import deploy, link, linker


@pytest.fixture
def escrow_deployer(solc_deployer, w3, manifest_dir):
    escrow_manifest_path = ASSETS_DIR / "escrow" / "1.0.3.json"
    return solc_deployer(escrow_manifest_path), w3


def test_linker(escrow_deployer):
    # todo test multiple links in one type
    deployer, w3 = escrow_deployer
    assert isinstance(deployer, Deployer)
    with pytest.raises(DeployerError):
        deployer.deploy("Escrow")

    escrow_strategy = linker(
        deploy("SafeSendLib"),
        link("Escrow", "SafeSendLib"),
        deploy("Escrow", w3.eth.accounts[0]),
    )
    assert hasattr(escrow_strategy, "__call__")
    deployer.register_strategy("Escrow", escrow_strategy)
    linked_escrow_package = deployer.deploy("Escrow")
    assert isinstance(linked_escrow_package, Package)
    linked_escrow_factory = linked_escrow_package.get_contract_factory("Escrow")
    assert linked_escrow_factory.needs_bytecode_linking is False


def test_linker_with_from(escrow_deployer):
    deployer, w3 = escrow_deployer
    escrow_strategy = linker(
        deploy("SafeSendLib"),
        link("Escrow", "SafeSendLib"),
        deploy("Escrow", w3.eth.accounts[0], transaction={"from": w3.eth.accounts[5]}),
    )
    deployer.register_strategy("Escrow", escrow_strategy)
    linked_escrow_package = deployer.deploy("Escrow")
    escrow_instance = linked_escrow_package.deployments.get_instance("Escrow")
    assert escrow_instance.functions.sender().call() == w3.eth.accounts[5]